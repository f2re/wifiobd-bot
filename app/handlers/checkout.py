"""
Checkout and order creation handlers
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from app.states.checkout import CheckoutStates
from app.services.cart import cart_service
from app.services.order import order_service
from app.services.user import user_service
from app.keyboards.inline import (
    checkout_confirm_keyboard,
    skip_keyboard,
    back_to_main_menu_keyboard
)
from app.utils.logger import get_logger
from app.utils.formatting import format_price

logger = get_logger(__name__)

router = Router()


@router.callback_query(F.data == "checkout")
async def start_checkout(callback: CallbackQuery, state: FSMContext, db: AsyncSession):
    """Start checkout process - auto-fill and confirm"""
    try:
        user_id = callback.from_user.id

        # Get cart
        cart = await cart_service.get_cart(user_id)

        if not cart["items"]:
            await callback.answer("🛒 Корзина пуста", show_alert=True)
            return

        # Get user info from database
        user = await user_service.get_user(db, user_id)

        # Auto-fill data from Telegram
        telegram_user = callback.from_user

        # Name: first_name + last_name or just first_name
        full_name = telegram_user.first_name
        if telegram_user.last_name:
            full_name += f" {telegram_user.last_name}"

        # Phone from database if available
        phone = user.phone if user and user.phone else None

        # Email from database or generate from username
        email = None
        if user and user.email:
            email = user.email
        elif telegram_user.username:
            email = f"{telegram_user.username}@telegram.user"

        # Store data in state
        await state.update_data(
            name=full_name,
            phone=phone,
            email=email,
            address="Самовывоз",
            needs_phone=phone is None  # Flag if we need to ask for phone
        )

        # If no phone - ask for it, otherwise go straight to confirmation
        if phone is None:
            await ask_for_phone(callback.message, state, cart['total'])
        else:
            await show_order_confirmation(callback.message, state, is_callback=True)

        await callback.answer()

    except Exception as e:
        logger.error(f"Error starting checkout: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)


async def ask_for_phone(message: Message, state: FSMContext, total: float):
    """Ask user to share phone contact"""
    await state.set_state(CheckoutStates.waiting_phone)

    # Create keyboard with contact sharing button
    contact_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Поделиться контактом", request_contact=True)],
            [KeyboardButton(text="✏️ Ввести номер вручную")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    text = f"""
📝 <b>Оформление заказа</b>

Сумма к оплате: <b>{format_price(total)}</b>

📞 <b>Укажите номер телефона</b>

Нажмите "📱 Поделиться контактом" для автоматической отправки вашего номера, или выберите "✏️ Ввести номер вручную".
"""

    if hasattr(message, 'edit_text'):
        # Callback message - delete and send new
        try:
            await message.delete()
        except:
            pass

    await message.answer(
        text,
        reply_markup=contact_keyboard,
        parse_mode="HTML"
    )


@router.message(CheckoutStates.waiting_phone, F.contact)
async def process_contact(message: Message, state: FSMContext, db: AsyncSession):
    """Process shared contact"""
    contact = message.contact

    # Verify it's the user's own contact
    if contact.user_id != message.from_user.id:
        await message.answer(
            "❌ Пожалуйста, поделитесь своим контактом, а не контактом другого пользователя.",
            reply_markup=ReplyKeyboardRemove()
        )
        return

    phone = contact.phone_number

    # Ensure phone starts with +
    if not phone.startswith('+'):
        phone = f"+{phone}"

    await state.update_data(phone=phone, needs_phone=False)

    # Save phone to user profile
    await user_service.update_phone(db, message.from_user.id, phone)

    # Remove keyboard
    await message.answer(
        "✅ Номер телефона сохранен!",
        reply_markup=ReplyKeyboardRemove()
    )

    # Show confirmation
    await show_order_confirmation(message, state, is_callback=False)


@router.message(CheckoutStates.waiting_phone, F.text == "✏️ Ввести номер вручную")
async def ask_manual_phone(message: Message, state: FSMContext):
    """Ask for manual phone input"""
    await state.set_state(CheckoutStates.waiting_phone_manual)

    await message.answer(
        "📝 Введите номер телефона в формате:\n+7XXXXXXXXXX или 8XXXXXXXXXX",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="HTML"
    )


@router.message(CheckoutStates.waiting_phone_manual)
async def process_phone_manual(message: Message, state: FSMContext, db: AsyncSession):
    """Process manually entered phone"""
    phone = message.text.strip()

    # Simple phone validation
    phone_digits = ''.join(filter(str.isdigit, phone))

    if len(phone_digits) < 10:
        await message.answer("❌ Неверный формат телефона. Пожалуйста, введите корректный номер.")
        return

    # Format phone
    if phone.startswith('8'):
        phone = f"+7{phone_digits[1:]}"
    elif not phone.startswith('+'):
        phone = f"+{phone_digits}"

    await state.update_data(phone=phone, needs_phone=False)

    # Save phone to user profile
    await user_service.update_phone(db, message.from_user.id, phone)

    await message.answer("✅ Номер телефона сохранен!")

    # Show confirmation
    await show_order_confirmation(message, state, is_callback=False)


async def show_order_confirmation(message: Message, state: FSMContext, is_callback: bool = False):
    """Show order confirmation with pre-filled data"""
    data = await state.get_data()
    user_id = message.from_user.id if hasattr(message, 'from_user') else message.chat.id

    # Get cart
    cart = await cart_service.get_cart(user_id)

    # Build order summary
    items_text = []
    for item in cart["items"]:
        product = item["product"]
        if isinstance(product, dict):
            name = product.get("name", "Товар")
            price = product.get("price", 0)
        else:
            name = product.name
            price = product.price

        items_text.append(
            f"• {name}\n"
            f"  {format_price(price)} × {item['quantity']} = {format_price(item['subtotal'])}"
        )

    text = f"""
✅ <b>Подтверждение заказа</b>

<b>Ваши данные:</b>
👤 Имя: {data.get('name', 'Не указано')}
📞 Телефон: {data.get('phone', 'Не указан')}
📧 Email: {data.get('email', 'Не указан')}
📍 Доставка: {data.get('address', 'Самовывоз')}

<b>Товары:</b>
{chr(10).join(items_text)}

━━━━━━━━━━━━━━━━━
💰 <b>Итого: {format_price(cart['total'])}</b>

Проверьте данные и подтвердите заказ для перехода к оплате.
"""

    await state.set_state(CheckoutStates.confirm)

    # Create inline keyboard with edit options
    builder = InlineKeyboardBuilder()

    builder.button(text="✅ Подтвердить и оплатить", callback_data="confirm_order")
    builder.button(text="✏️ Изменить адрес", callback_data="edit_address")
    builder.button(text="✏️ Изменить имя", callback_data="edit_name")
    if data.get('phone'):
        builder.button(text="📞 Изменить телефон", callback_data="edit_phone")
    builder.button(text="❌ Отменить", callback_data="cancel_order")

    builder.adjust(1)

    if is_callback:
        try:
            await message.edit_text(
                text,
                reply_markup=builder.as_markup(),
                parse_mode="HTML"
            )
        except TelegramBadRequest:
            await message.answer(
                text,
                reply_markup=builder.as_markup(),
                parse_mode="HTML"
            )
    else:
        await message.answer(
            text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )


# Edit handlers
@router.callback_query(F.data == "edit_name", CheckoutStates.confirm)
async def edit_name(callback: CallbackQuery, state: FSMContext):
    """Edit customer name"""
    await state.set_state(CheckoutStates.waiting_name)

    await callback.message.edit_text(
        "📝 Введите ваше имя:",
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(CheckoutStates.waiting_name)
async def process_name_edit(message: Message, state: FSMContext):
    """Process edited name"""
    name = message.text.strip()

    if len(name) < 2:
        await message.answer("❌ Имя слишком короткое. Пожалуйста, введите корректное имя.")
        return

    await state.update_data(name=name)
    await show_order_confirmation(message, state, is_callback=False)


@router.callback_query(F.data == "edit_phone", CheckoutStates.confirm)
async def edit_phone(callback: CallbackQuery, state: FSMContext):
    """Edit phone number"""
    data = await state.get_data()
    cart = await cart_service.get_cart(callback.from_user.id)

    await ask_for_phone(callback.message, state, cart['total'])
    await callback.answer()


@router.callback_query(F.data == "edit_address", CheckoutStates.confirm)
async def edit_address(callback: CallbackQuery, state: FSMContext):
    """Edit delivery address"""
    await state.set_state(CheckoutStates.waiting_address)

    await callback.message.edit_text(
        "📍 Введите адрес доставки или нажмите кнопку ниже для самовывоза:",
        reply_markup=skip_keyboard("skip_address"),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "skip_address", CheckoutStates.waiting_address)
async def skip_address(callback: CallbackQuery, state: FSMContext):
    """Skip address (pickup)"""
    await state.update_data(address="Самовывоз")
    await show_order_confirmation(callback.message, state, is_callback=True)
    await callback.answer()


@router.message(CheckoutStates.waiting_address)
async def process_address_edit(message: Message, state: FSMContext):
    """Process edited address"""
    address = message.text.strip()

    if len(address) < 5:
        await message.answer("❌ Адрес слишком короткий. Пожалуйста, укажите полный адрес.")
        return

    await state.update_data(address=address)
    await show_order_confirmation(message, state, is_callback=False)


@router.callback_query(F.data == "cancel_order", CheckoutStates.confirm)
async def cancel_order(callback: CallbackQuery, state: FSMContext):
    """Cancel order creation"""
    await state.clear()

    text = "❌ <b>Заказ отменен</b>\n\nВы можете продолжить покупки в каталоге."

    await callback.message.edit_text(
        text,
        reply_markup=back_to_main_menu_keyboard(),
        parse_mode="HTML"
    )

    await callback.answer("Заказ отменен")
