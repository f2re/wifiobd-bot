"""
Payment processing handlers
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.cart import cart_service
from app.services.order import order_service
from app.services.yoomoney import yoomoney_service
from app.services.opencart import opencart_service
from app.services.user import user_service
from app.keyboards.inline import payment_keyboard, back_to_main_menu_keyboard
from app.utils.logger import get_logger
from app.utils.formatting import format_price
from app.states.checkout import CheckoutStates

logger = get_logger(__name__)

router = Router()


@router.callback_query(F.data == "confirm_order", CheckoutStates.confirm)
async def confirm_and_create_order(callback: CallbackQuery, state: FSMContext, db: AsyncSession):
    """Confirm order and proceed to payment"""
    try:
        user_id = callback.from_user.id

        # Get checkout data
        checkout_data = await state.get_data()

        # Get cart
        cart = await cart_service.get_cart(user_id)

        if not cart["items"]:
            await callback.answer("❌ Корзина пуста", show_alert=True)
            await state.clear()
            return

        # Create order in database
        order = await order_service.create_order(
            db=db,
            user_id=user_id,
            cart=cart,
            delivery_data=checkout_data
        )

        # Create payment
        payment = yoomoney_service.create_payment(
            order_id=order.id,
            amount=float(order.amount)
        )

        # Update order with payment label
        await order_service.update_payment_label(db, order.id, payment["label"])

        # Clear FSM state
        await state.clear()

        # Send payment message
        text = f"""
💰 <b>Заказ №{order.id} создан</b>

Сумма к оплате: <b>{format_price(order.amount)}</b>

Нажмите кнопку "Оплатить" для перехода на страницу оплаты.
После завершения оплаты вернитесь в бот и нажмите "Проверить оплату".

⚠️ <b>Важно:</b> Не закрывайте это сообщение до завершения оплаты!
"""

        await callback.message.edit_text(
            text,
            reply_markup=payment_keyboard(order.id, payment["payment_url"]),
            parse_mode="HTML"
        )

        await callback.answer("✅ Заказ создан!")

        logger.info(f"Order {order.id} created for user {user_id}, amount: {order.amount}")

    except Exception as e:
        logger.error(f"Error creating order: {e}")
        await callback.answer("❌ Произошла ошибка при создании заказа", show_alert=True)
        await state.clear()


@router.callback_query(F.data.startswith("checkpay:"))
async def check_payment(callback: CallbackQuery, db: AsyncSession):
    """Check payment status"""
    try:
        order_id = int(callback.data.split(":")[1])

        # Get order
        order = await order_service.get_order_with_user(db, order_id)

        if not order:
            await callback.answer("❌ Заказ не найден", show_alert=True)
            return

        # Check if already paid
        if order.status == "paid":
            await callback.answer("✅ Заказ уже оплачен", show_alert=True)
            return

        # Check payment status with YooMoney
        payment_status = yoomoney_service.check_payment(order.yoomoney_label)

        if payment_status["status"] == "success":
            # Payment confirmed!
            await order_service.update_status(db, order.id, "paid")

            # Clear cart
            await cart_service.clear_cart(order.user_id)

            # Try to create order in OpenCart
            try:
                # Get or create OpenCart customer
                user = order.user
                if not user.opencart_customer_id:
                    # Create customer in OpenCart
                    oc_customer_data = {
                        "firstname": order.customer_name or user.first_name,
                        "lastname": "Customer",
                        "email": order.customer_email or f"tg{user.id}@wifiobd.ru",
                        "telephone": order.customer_phone or ""
                    }

                    oc_customer = await opencart_service.create_customer(oc_customer_data)
                    if oc_customer.get("customer_id"):
                        await user_service.update_opencart_id(db, user.id, oc_customer["customer_id"])
                        user.opencart_customer_id = oc_customer["customer_id"]

                # Prepare OpenCart order data
                oc_products = []
                for item in order.items:
                    oc_products.append({
                        "product_id": item["product_id"],
                        "name": item["name"],
                        "model": item["model"],
                        "quantity": item["quantity"],
                        "price": item["price"]
                    })

                oc_order_data = {
                    "customer_id": user.opencart_customer_id or 0,
                    "firstname": order.customer_name or user.first_name or "Customer",
                    "lastname": "Telegram",
                    "email": order.customer_email or f"tg{user.id}@wifiobd.ru",
                    "telephone": order.customer_phone or "",
                    "payment_method": "YooMoney",
                    "shipping_method": "Самовывоз" if order.delivery_address == "Самовывоз" else "Доставка",
                    "comment": order.delivery_comment or "",
                    "products": oc_products,
                    "payment_address": {
                        "payment_firstname": order.customer_name or user.first_name or "Customer",
                        "payment_lastname": "Telegram",
                        "payment_address_1": order.delivery_address or "",
                        "payment_city": "Moscow",
                        "payment_country": "Russia"
                    },
                    "shipping_address": {
                        "shipping_firstname": order.customer_name or user.first_name or "Customer",
                        "shipping_lastname": "Telegram",
                        "shipping_address_1": order.delivery_address or "",
                        "shipping_city": "Moscow",
                        "shipping_country": "Russia"
                    },
                    "order_status_id": 2  # Processing
                }

                # Create order in OpenCart
                oc_order = await opencart_service.create_order(oc_order_data)

                if oc_order.get("order_id"):
                    await order_service.update_opencart_order_id(db, order.id, oc_order["order_id"])
                    logger.info(f"Created OpenCart order {oc_order['order_id']} for bot order {order.id}")

            except Exception as oc_error:
                logger.error(f"Failed to create OpenCart order: {oc_error}")
                # Continue anyway, order is paid in bot

            # Success message
            text = f"""
✅ <b>Оплата успешна!</b>

Заказ №{order.id} оплачен и принят в обработку.

💰 Сумма: {format_price(order.amount)}
📞 Телефон: {order.customer_phone}

В ближайшее время с вами свяжется наш менеджер для уточнения деталей доставки.

<b>Спасибо за покупку!</b> 🎉
"""

            await callback.message.edit_text(
                text,
                reply_markup=back_to_main_menu_keyboard(),
                parse_mode="HTML"
            )

            await callback.answer("✅ Оплата подтверждена!", show_alert=True)

            logger.info(f"Payment confirmed for order {order.id}")

        elif payment_status["status"] == "pending":
            await callback.answer(
                "⏳ Оплата еще не поступила.\nПопробуйте через минуту.",
                show_alert=True
            )

        else:
            await callback.answer(
                "❌ Не удалось проверить статус оплаты.\nПопробуйте позже.",
                show_alert=True
            )

    except Exception as e:
        logger.error(f"Error checking payment: {e}")
        await callback.answer("❌ Произошла ошибка при проверке оплаты", show_alert=True)


@router.callback_query(F.data.startswith("cancelpay:"))
async def cancel_payment(callback: CallbackQuery, db: AsyncSession):
    """Cancel payment and order"""
    try:
        order_id = int(callback.data.split(":")[1])

        # Get order
        order = await order_service.get_order(db, order_id)

        if not order:
            await callback.answer("❌ Заказ не найден", show_alert=True)
            return

        # Check if already paid
        if order.status == "paid":
            await callback.answer("❌ Заказ уже оплачен. Для возврата обратитесь в поддержку.", show_alert=True)
            return

        # Cancel order
        await order_service.update_status(db, order.id, "cancelled")

        text = f"""
❌ <b>Заказ №{order.id} отменен</b>

Вы можете создать новый заказ в любое время.
"""

        await callback.message.edit_text(
            text,
            reply_markup=back_to_main_menu_keyboard(),
            parse_mode="HTML"
        )

        await callback.answer("Заказ отменен")

        logger.info(f"Order {order.id} cancelled by user")

    except Exception as e:
        logger.error(f"Error cancelling payment: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)


@router.callback_query(F.data == "my_orders")
async def show_my_orders(callback: CallbackQuery, db: AsyncSession):
    """Show user's order history"""
    try:
        user_id = callback.from_user.id

        # Get user's orders
        orders = await order_service.get_user_orders(db, user_id, limit=10)

        if not orders:
            text = "📦 <b>История заказов</b>\n\nУ вас пока нет заказов."
            await callback.message.edit_text(
                text,
                reply_markup=back_to_main_menu_keyboard(),
                parse_mode="HTML"
            )
            await callback.answer()
            return

        # Build orders list
        text = "📦 <b>Ваши заказы:</b>\n\n"

        for order in orders:
            status_emoji = {"pending": "⏳", "paid": "✅", "cancelled": "❌", "completed": "🎉"}.get(order.status, "❓")
            status_text = {"pending": "Ожидает оплаты", "paid": "Оплачен", "cancelled": "Отменен", "completed": "Выполнен"}.get(order.status, "Неизвестно")

            text += f"""
{status_emoji} <b>Заказ #{order.id}</b>
💰 Сумма: {format_price(order.amount)}
📅 Дата: {order.created_at.strftime('%d.%m.%Y %H:%M')}
📊 Статус: {status_text}
━━━━━━━━━━━━
"""

        await callback.message.edit_text(
            text,
            reply_markup=back_to_main_menu_keyboard(),
            parse_mode="HTML"
        )

        await callback.answer()

    except Exception as e:
        logger.error(f"Error showing orders: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)
