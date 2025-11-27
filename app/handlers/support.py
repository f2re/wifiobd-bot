"""
Support ticket system handlers
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.states.admin import SupportStates
from app.database.models import SupportTicket
from app.keyboards.inline import (
    back_to_main_menu_keyboard,
    admin_ticket_keyboard
)
from app.filters.admin import IsAdmin
from app.utils.logger import get_logger
from app.utils.formatting import format_date
from app.bot import bot
from config import settings

logger = get_logger(__name__)

router = Router()


@router.callback_query(F.data == "support")
async def support_start(callback: CallbackQuery, state: FSMContext):
    """Start support ticket creation"""
    await state.set_state(SupportStates.waiting_message)

    text = """
💬 <b>Обращение в службу поддержки</b>

Опишите вашу проблему или вопрос.
Наши специалисты ответят вам в ближайшее время.
"""

    await callback.message.edit_text(
        text,
        parse_mode="HTML"
    )

    await callback.answer()


@router.message(SupportStates.waiting_message)
async def support_save_ticket(message: Message, state: FSMContext, db: AsyncSession):
    """Save support ticket"""
    try:
        user_id = message.from_user.id
        ticket_text = message.text

        # Create ticket in database
        ticket = SupportTicket(
            user_id=user_id,
            message=ticket_text,
            status="open"
        )

        db.add(ticket)
        await db.commit()
        await db.refresh(ticket)

        # Notify admins
        for admin_id in settings.ADMIN_IDS:
            try:
                user_name = message.from_user.first_name
                username = f"@{message.from_user.username}" if message.from_user.username else ""

                admin_text = f"""
🆘 <b>Новое обращение #{ticket.id}</b>

👤 От: {user_name} {username} (ID: {user_id})
📅 Дата: {format_date(ticket.created_at)}

<b>Сообщение:</b>
{ticket_text}
"""

                await bot.send_message(
                    admin_id,
                    admin_text,
                    reply_markup=admin_ticket_keyboard(ticket.id),
                    parse_mode="HTML"
                )

            except Exception as notify_error:
                logger.warning(f"Failed to notify admin {admin_id}: {notify_error}")

        # Confirm to user
        await message.answer(
            f"""
✅ <b>Обращение #{ticket.id} создано</b>

Ваше сообщение получено.
Ожидайте ответа от специалиста.

Мы стараемся отвечать в течение 24 часов.
""",
            reply_markup=back_to_main_menu_keyboard(),
            parse_mode="HTML"
        )

        await state.clear()

        logger.info(f"Support ticket {ticket.id} created by user {user_id}")

    except Exception as e:
        logger.error(f"Error creating support ticket: {e}")
        await message.answer("❌ Произошла ошибка при создании обращения")
        await state.clear()


# Admin handlers for support tickets

admin_router = Router()
admin_router.message.filter(IsAdmin())
admin_router.callback_query.filter(IsAdmin())


@admin_router.callback_query(F.data == "admin:tickets")
async def admin_show_tickets(callback: CallbackQuery, db: AsyncSession):
    """Show all support tickets"""
    try:
        # Get open tickets
        query = (
            select(SupportTicket)
            .where(SupportTicket.status == "open")
            .order_by(SupportTicket.created_at.desc())
        )
        result = await db.execute(query)
        tickets = result.scalars().all()

        if not tickets:
            text = "💬 <b>Обращения в поддержку</b>\n\nНет открытых обращений."
        else:
            text = "💬 <b>Открытые обращения:</b>\n\n"

            for ticket in tickets[:20]:  # Limit to 20 most recent
                text += f"""
🆘 <b>#{ticket.id}</b> | User ID: {ticket.user_id}
📅 {format_date(ticket.created_at)}
📝 {ticket.message[:50]}{'...' if len(ticket.message) > 50 else ''}
/ticket_{ticket.id}

"""

        text += "\nНажмите /ticket_ID для просмотра и ответа"

        from app.keyboards.inline import admin_menu_keyboard
        await callback.message.edit_text(
            text,
            reply_markup=admin_menu_keyboard(),
            parse_mode="HTML"
        )

        await callback.answer()

    except Exception as e:
        logger.error(f"Error showing tickets: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)


@admin_router.message(F.text.regexp(r"/ticket_(\d+)"))
async def admin_show_ticket_details(message: Message, db: AsyncSession):
    """Show ticket details"""
    try:
        # Extract ticket ID
        ticket_id = int(message.text.split("_")[1])

        # Get ticket
        query = select(SupportTicket).where(SupportTicket.id == ticket_id)
        result = await db.execute(query)
        ticket = result.scalar_one_or_none()

        if not ticket:
            await message.answer("❌ Обращение не найдено")
            return

        # Get user info
        from app.database.models import User
        query = select(User).where(User.id == ticket.user_id)
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        user_name = user.first_name if user else "Unknown"
        username = f"@{user.username}" if user and user.username else ""

        text = f"""
🆘 <b>Обращение #{ticket.id}</b>

👤 От: {user_name} {username} (ID: {ticket.user_id})
📅 Создано: {format_date(ticket.created_at)}
📊 Статус: {ticket.status}

<b>Сообщение:</b>
{ticket.message}
"""

        if ticket.admin_response:
            text += f"\n\n<b>Ответ администратора:</b>\n{ticket.admin_response}"
            text += f"\n📅 Отвечено: {format_date(ticket.answered_at)}"

        await message.answer(
            text,
            reply_markup=admin_ticket_keyboard(ticket.id),
            parse_mode="HTML"
        )

    except Exception as e:
        logger.error(f"Error showing ticket details: {e}")
        await message.answer("❌ Произошла ошибка")


@admin_router.callback_query(F.data.startswith("admin:reply:"))
async def admin_reply_ticket_start(callback: CallbackQuery, state: FSMContext):
    """Start replying to ticket"""
    try:
        ticket_id = int(callback.data.split(":")[2])

        await state.set_state(SupportStates.waiting_response)
        await state.update_data(ticket_id=ticket_id)

        await callback.message.answer(
            f"✏️ <b>Ответ на обращение #{ticket_id}</b>\n\nВведите текст ответа:",
            parse_mode="HTML"
        )

        await callback.answer()

    except Exception as e:
        logger.error(f"Error starting ticket reply: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)


@admin_router.message(SupportStates.waiting_response)
async def admin_send_ticket_response(message: Message, state: FSMContext, db: AsyncSession):
    """Send ticket response to user"""
    try:
        data = await state.get_data()
        ticket_id = data.get("ticket_id")

        if not ticket_id:
            await message.answer("❌ Ошибка: обращение не найдено")
            await state.clear()
            return

        # Get ticket
        query = select(SupportTicket).where(SupportTicket.id == ticket_id)
        result = await db.execute(query)
        ticket = result.scalar_one_or_none()

        if not ticket:
            await message.answer("❌ Обращение не найдено")
            await state.clear()
            return

        # Update ticket
        ticket.admin_response = message.text
        ticket.status = "answered"
        ticket.answered_at = datetime.utcnow()

        await db.commit()

        # Send response to user
        try:
            await bot.send_message(
                ticket.user_id,
                f"""
💬 <b>Ответ на ваше обращение #{ticket.id}</b>

<b>Ваш вопрос:</b>
{ticket.message}

<b>Ответ специалиста:</b>
{message.text}

Если у вас остались вопросы, создайте новое обращение.
""",
                parse_mode="HTML"
            )

            await message.answer(
                f"✅ Ответ отправлен пользователю {ticket.user_id}",
                reply_markup=admin_ticket_keyboard(ticket.id)
            )

            logger.info(f"Admin {message.from_user.id} replied to ticket {ticket.id}")

        except Exception as send_error:
            logger.error(f"Failed to send response to user: {send_error}")
            await message.answer("❌ Не удалось отправить ответ пользователю (возможно, заблокировал бота)")

        await state.clear()

    except Exception as e:
        logger.error(f"Error sending ticket response: {e}")
        await message.answer("❌ Произошла ошибка")
        await state.clear()


@admin_router.callback_query(F.data.startswith("admin:close_ticket:"))
async def admin_close_ticket(callback: CallbackQuery, db: AsyncSession):
    """Close support ticket"""
    try:
        ticket_id = int(callback.data.split(":")[2])

        # Get ticket
        query = select(SupportTicket).where(SupportTicket.id == ticket_id)
        result = await db.execute(query)
        ticket = result.scalar_one_or_none()

        if not ticket:
            await callback.answer("❌ Обращение не найдено", show_alert=True)
            return

        # Update status
        ticket.status = "closed"
        ticket.closed_at = datetime.utcnow()

        await db.commit()

        await callback.answer("✅ Обращение закрыто", show_alert=True)

        # Update message
        await callback.message.edit_text(
            f"✅ <b>Обращение #{ticket.id} закрыто</b>",
            parse_mode="HTML"
        )

        logger.info(f"Ticket {ticket.id} closed by admin {callback.from_user.id}")

    except Exception as e:
        logger.error(f"Error closing ticket: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)


# Include admin router
router.include_router(admin_router)
