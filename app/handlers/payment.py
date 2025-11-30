"""
Payment processing handlers for VK bot with YooKassa
"""
from vkbottle.bot import Bot, Message
from vkbottle import Keyboard, Callback, OpenLink, KeyboardButtonColor
from decimal import Decimal

from app.services.cart import cart_service
from app.services.yookassa_service import yookassa_service
from app.keyboards.inline import VKKeyboards
from app.utils.logger import get_logger
from app.utils.formatting import format_price

logger = get_logger(__name__)


def register_handlers(bot: Bot):
    """Register payment handlers"""

    @bot.on.message(payload={'action': 'pay_yookassa'})
    async def create_payment(message: Message):
        """Create YooKassa payment and send payment link"""
        try:
            user_id = message.from_id

            # Get cart
            cart = await cart_service.get_cart(user_id)

            if not cart["items"]:
                await message.answer("🛒 Корзина пуста", keyboard=VKKeyboards.main_menu())
                return

            # Create payment in YooKassa
            amount = Decimal(str(cart['total']))
            description = f"Оплата заказа для пользователя VK{user_id}"

            payment = await yookassa_service.create_payment(
                amount=amount,
                description=description,
                metadata={"vk_user_id": user_id, "cart_total": str(cart['total'])}
            )

            if not payment:
                await message.answer(
                    "❌ Не удалось создать платеж. Попробуйте позже.",
                    keyboard=VKKeyboards.main_menu()
                )
                return

            # Save payment ID in Redis for later verification
            # TODO: Implement payment tracking in database

            # Send payment link to user
            text = f"""
💳 <b>Оплата заказа</b>

💰 Сумма к оплате: <b>{format_price(cart['total'])}</b>

Нажмите кнопку ниже для перехода на страницу оплаты.

После успешной оплаты нажмите "Проверить оплату".

ID платежа: {payment['id']}
"""

            # Create keyboard with payment link
            keyboard = Keyboard(inline=True)
            keyboard.add(OpenLink(label="💳 Оплатить", link=payment['confirmation_url']))
            keyboard.row()
            keyboard.add(Callback(label="✅ Проверить оплату", payload={'action': 'check_payment', 'id': payment['id']}))
            keyboard.add(Callback(label="❌ Отменить", payload={'action': 'cancel_payment'}))

            await message.answer(text, keyboard=keyboard.get_json())

            logger.info(f"Payment {payment['id']} created for VK user {user_id}, amount: {amount}")

        except Exception as e:
            logger.error(f"Error creating payment: {e}", exc_info=True)
            await message.answer("❌ Произошла ошибка при создании платежа")

    @bot.on.message(payload={'action': 'check_payment'})
    async def check_payment(message: Message):
        """Check payment status"""
        try:
            payload = message.get_payload_json()
            payment_id = payload.get('id')

            if not payment_id:
                await message.answer("❌ Ошибка: ID платежа не указан")
                return

            # Check payment status
            status = await yookassa_service.check_payment_status(payment_id)

            if status == "succeeded":
                user_id = message.from_id

                # Clear cart
                await cart_service.clear_cart(user_id)

                # Success message
                text = f"""
✅ <b>Оплата успешна!</b>

Ваш заказ принят в обработку.

В ближайшее время с вами свяжется наш менеджер для уточнения деталей доставки.

<b>Спасибо за покупку!</b> 🎉

ID платежа: {payment_id}
"""

                await message.answer(text, keyboard=VKKeyboards.main_menu())

                logger.info(f"Payment {payment_id} confirmed for VK user {user_id}")

            elif status == "pending" or status == "waiting_for_capture":
                await message.answer(
                    "⏳ Оплата еще обрабатывается.\nПопробуйте проверить через минуту.",
                    keyboard=VKKeyboards.main_menu()
                )
            elif status == "canceled":
                await message.answer(
                    "❌ Платеж был отменен.",
                    keyboard=VKKeyboards.main_menu()
                )
            else:
                await message.answer(
                    f"❓ Статус платежа: {status}\nПопробуйте проверить позже.",
                    keyboard=VKKeyboards.main_menu()
                )

        except Exception as e:
            logger.error(f"Error checking payment: {e}", exc_info=True)
            await message.answer("❌ Произошла ошибка при проверке платежа")

    @bot.on.message(payload={'action': 'cancel_payment'})
    async def cancel_payment(message: Message):
        """Cancel payment"""
        await message.answer(
            "❌ Оплата отменена.\n\nВы можете создать новый заказ в любое время.",
            keyboard=VKKeyboards.main_menu()
        )

    logger.info("Payment handlers registered")
