"""
Admin panel handlers
"""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.filters.admin import IsAdmin
from app.states.admin import AdminStates
from app.services.order import order_service
from app.services.user import user_service
from app.database.models import Order, User, SupportTicket
from app.keyboards.inline import (
    admin_menu_keyboard,
    admin_order_keyboard,
    admin_ticket_keyboard,
    back_to_main_menu_keyboard
)
from app.utils.logger import get_logger
from app.utils.formatting import format_order_summary, format_date, format_price
from app.bot import bot

logger = get_logger(__name__)

router = Router()
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


@router.message(Command("admin"))
async def admin_panel(message: Message):
    """Show admin panel"""
    text = """
⚙️ <b>Админ-панель</b>

Выберите раздел:
"""

    await message.answer(
        text,
        reply_markup=admin_menu_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "admin:menu")
async def admin_menu_callback(callback: CallbackQuery):
    """Show admin menu"""
    text = """
⚙️ <b>Админ-панель</b>

Выберите раздел:
"""

    await callback.message.edit_text(
        text,
        reply_markup=admin_menu_keyboard(),
        parse_mode="HTML"
    )

    await callback.answer()


@router.callback_query(F.data == "admin:orders")
async def admin_orders(callback: CallbackQuery, db: AsyncSession):
    """Show recent orders"""
    try:
        orders = await order_service.get_recent_orders(db, limit=15)

        if not orders:
            text = "📋 <b>Заказы</b>\n\nНет заказов."
            await callback.message.edit_text(
                text,
                reply_markup=admin_menu_keyboard(),
                parse_mode="HTML"
            )
            await callback.answer()
            return

        text = "📋 <b>Последние заказы:</b>\n\n"

        for order in orders:
            status_emoji = {
                "pending": "⏳",
                "paid": "✅",
                "cancelled": "❌",
                "refunded": "💸",
                "completed": "🎉"
            }.get(order.status, "❓")

            user_name = order.user.first_name if order.user else "Unknown"

            text += f"""
{status_emoji} <b>#{order.id}</b> | {user_name} | {format_price(order.amount)}
📅 {format_date(order.created_at)}
/order_{order.id}

"""

        text += "\nНажмите /order_ID для просмотра деталей"

        await callback.message.edit_text(
            text,
            reply_markup=admin_menu_keyboard(),
            parse_mode="HTML"
        )

        await callback.answer()

    except Exception as e:
        logger.error(f"Error showing admin orders: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)


@router.message(Command(commands=["order"]), F.text.regexp(r"/order_(\d+)"))
async def admin_order_details(message: Message, db: AsyncSession):
    """Show order details"""
    try:
        # Extract order ID from command
        order_id = int(message.text.split("_")[1])

        order = await order_service.get_order_with_user(db, order_id)

        if not order:
            await message.answer("❌ Заказ не найден")
            return

        # Format order details
        text = format_order_summary(order)

        # Add OpenCart info if available
        if order.opencart_order_id:
            text += f"\n🔗 <b>OpenCart Order ID:</b> {order.opencart_order_id}"

        await message.answer(
            text,
            reply_markup=admin_order_keyboard(order.id, order.status, order.user_id),
            parse_mode="HTML"
        )

    except Exception as e:
        logger.error(f"Error showing order details: {e}")
        await message.answer("❌ Произошла ошибка")


@router.callback_query(F.data.startswith("admin:complete:"))
async def admin_complete_order(callback: CallbackQuery, db: AsyncSession):
    """Mark order as completed"""
    try:
        order_id = int(callback.data.split(":")[2])

        success = await order_service.update_status(db, order_id, "completed")

        if success:
            await callback.answer("✅ Заказ отмечен как выполненный", show_alert=True)

            # Notify customer
            order = await order_service.get_order_with_user(db, order_id)
            if order:
                try:
                    await bot.send_message(
                        order.user_id,
                        f"✅ <b>Заказ #{order.id} выполнен!</b>\n\nСпасибо за покупку!",
                        parse_mode="HTML"
                    )
                except:
                    pass

            # Refresh view
            text = format_order_summary(order)
            await callback.message.edit_text(
                text,
                reply_markup=admin_order_keyboard(order.id, "completed", order.user_id),
                parse_mode="HTML"
            )
        else:
            await callback.answer("❌ Не удалось обновить статус", show_alert=True)

    except Exception as e:
        logger.error(f"Error completing order: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)


@router.callback_query(F.data.startswith("admin:cancel:"))
async def admin_cancel_order(callback: CallbackQuery, db: AsyncSession):
    """Cancel order"""
    try:
        order_id = int(callback.data.split(":")[2])

        success = await order_service.update_status(db, order_id, "cancelled")

        if success:
            await callback.answer("❌ Заказ отменен", show_alert=True)

            # Notify customer
            order = await order_service.get_order_with_user(db, order_id)
            if order:
                try:
                    await bot.send_message(
                        order.user_id,
                        f"❌ <b>Заказ #{order.id} отменен</b>\n\nПо всем вопросам обращайтесь в поддержку.",
                        parse_mode="HTML"
                    )
                except:
                    pass

            # Refresh view
            text = format_order_summary(order)
            await callback.message.edit_text(
                text,
                reply_markup=admin_order_keyboard(order.id, "cancelled", order.user_id),
                parse_mode="HTML"
            )
        else:
            await callback.answer("❌ Не удалось отменить заказ", show_alert=True)

    except Exception as e:
        logger.error(f"Error cancelling order: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)


@router.callback_query(F.data.startswith("admin:msg:"))
async def admin_message_user_start(callback: CallbackQuery, state: FSMContext):
    """Start sending message to user"""
    try:
        user_id = int(callback.data.split(":")[2])

        await state.set_state(AdminStates.waiting_message_to_user)
        await state.update_data(target_user_id=user_id)

        await callback.message.answer(
            f"💬 <b>Отправка сообщения пользователю {user_id}</b>\n\nВведите текст сообщения:",
            parse_mode="HTML"
        )

        await callback.answer()

    except Exception as e:
        logger.error(f"Error starting message to user: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)


@router.message(AdminStates.waiting_message_to_user)
async def admin_send_message_to_user(message: Message, state: FSMContext):
    """Send message to user"""
    try:
        data = await state.get_data()
        target_user_id = data.get("target_user_id")

        if not target_user_id:
            await message.answer("❌ Ошибка: пользователь не указан")
            await state.clear()
            return

        # Send message to user
        try:
            await bot.send_message(
                target_user_id,
                f"📨 <b>Сообщение от администрации:</b>\n\n{message.text}",
                parse_mode="HTML"
            )

            await message.answer(
                f"✅ Сообщение отправлено пользователю {target_user_id}",
                reply_markup=admin_menu_keyboard()
            )

            logger.info(f"Admin {message.from_user.id} sent message to user {target_user_id}")

        except Exception as send_error:
            logger.error(f"Failed to send message to user: {send_error}")
            await message.answer("❌ Не удалось отправить сообщение пользователю (возможно, заблокировал бота)")

        await state.clear()

    except Exception as e:
        logger.error(f"Error sending message to user: {e}")
        await message.answer("❌ Произошла ошибка")
        await state.clear()


@router.callback_query(F.data == "admin:users")
async def admin_users(callback: CallbackQuery, db: AsyncSession):
    """Show users statistics"""
    try:
        # Get total users count
        query = select(func.count(User.id))
        result = await db.execute(query)
        total_users = result.scalar()

        # Get recent users
        users = await user_service.get_all_users(db, limit=10)

        text = f"""
👥 <b>Пользователи</b>

📊 Всего пользователей: {total_users}

<b>Последние регистрации:</b>

"""

        for user in users:
            text += f"• {user.first_name} (@{user.username or 'no username'}) - {format_date(user.created_at)}\n"

        await callback.message.edit_text(
            text,
            reply_markup=admin_menu_keyboard(),
            parse_mode="HTML"
        )

        await callback.answer()

    except Exception as e:
        logger.error(f"Error showing users: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)


@router.callback_query(F.data == "admin:stats")
async def admin_stats(callback: CallbackQuery, db: AsyncSession):
    """Show statistics"""
    try:
        # Total users
        query = select(func.count(User.id))
        result = await db.execute(query)
        total_users = result.scalar()

        # Total orders
        query = select(func.count(Order.id))
        result = await db.execute(query)
        total_orders = result.scalar()

        # Total revenue (paid orders)
        query = select(func.sum(Order.amount)).where(Order.status == "paid")
        result = await db.execute(query)
        total_revenue = result.scalar() or 0

        # Pending orders
        query = select(func.count(Order.id)).where(Order.status == "pending")
        result = await db.execute(query)
        pending_orders = result.scalar()

        text = f"""
📊 <b>Статистика</b>

👥 Всего пользователей: {total_users}
📦 Всего заказов: {total_orders}
⏳ Ожидают оплаты: {pending_orders}

💰 Общая выручка: {format_price(total_revenue)}
"""

        await callback.message.edit_text(
            text,
            reply_markup=admin_menu_keyboard(),
            parse_mode="HTML"
        )

        await callback.answer()

    except Exception as e:
        logger.error(f"Error showing stats: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)


@router.callback_query(F.data == "admin:broadcast")
async def admin_broadcast_start(callback: CallbackQuery, state: FSMContext):
    """Start broadcast message"""
    await state.set_state(AdminStates.waiting_broadcast_message)

    text = """
📢 <b>Рассылка сообщения</b>

Введите текст сообщения для рассылки всем пользователям:

⚠️ Будьте осторожны! Сообщение будет отправлено всем пользователям бота.
"""

    await callback.message.edit_text(
        text,
        parse_mode="HTML"
    )

    await callback.answer()


@router.message(AdminStates.waiting_broadcast_message)
async def admin_broadcast_send(message: Message, state: FSMContext, db: AsyncSession):
    """Send broadcast message"""
    try:
        broadcast_text = message.text

        # Get all users
        users = await user_service.get_all_users(db, limit=10000)

        success_count = 0
        fail_count = 0

        status_message = await message.answer("📤 Начинаю рассылку...")

        for user in users:
            try:
                await bot.send_message(
                    user.id,
                    f"📢 <b>Сообщение от администрации:</b>\n\n{broadcast_text}",
                    parse_mode="HTML"
                )
                success_count += 1

                # Update status every 10 users
                if success_count % 10 == 0:
                    await status_message.edit_text(
                        f"📤 Рассылка: {success_count}/{len(users)}"
                    )

            except Exception as send_error:
                logger.warning(f"Failed to send broadcast to user {user.id}: {send_error}")
                fail_count += 1

        await status_message.edit_text(
            f"""
✅ <b>Рассылка завершена</b>

📨 Успешно отправлено: {success_count}
❌ Не удалось отправить: {fail_count}
""",
            reply_markup=admin_menu_keyboard(),
            parse_mode="HTML"
        )

        await state.clear()

        logger.info(f"Broadcast completed: {success_count} success, {fail_count} failed")

    except Exception as e:
        logger.error(f"Error sending broadcast: {e}")
        await message.answer("❌ Произошла ошибка при рассылке")
        await state.clear()
