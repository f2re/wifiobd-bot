"""
Checkout and order creation handlers
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
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
    """Start checkout process"""
    try:
        user_id = callback.from_user.id

        # Get cart
        cart = await cart_service.get_cart(user_id)

        if not cart["items"]:
            await callback.answer("🛒 Корзина пуста", show_alert=True)
            return

        # Get user info
        user = await user_service.get_user(db, user_id)

        # Start FSM
        await state.set_state(CheckoutStates.waiting_name)

        # Pre-fill name if available
        default_name = user.first_name if user else callback.from_user.first_name

        text = f"""
📝 <b>Оформление заказа</b>

Сумма к оплате: <b>{format_price(cart['total'])}</b>

<b>Шаг 1/4:</b> Введите ваше имя

Имя по умолчанию: {default_name}
"""

        await callback.message.edit_text(
            text,
            reply_markup=skip_keyboard("skip_name"),
            parse_mode="HTML"
        )

        # Store default name in state
        await state.update_data(default_name=default_name)

        await callback.answer()

    except Exception as e:
        logger.error(f"Error starting checkout: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)


@router.callback_query(F.data == "skip_name", CheckoutStates.waiting_name)
async def skip_name(callback: CallbackQuery, state: FSMContext):
    """Skip name input, use default"""
    data = await state.get_data()
    default_name = data.get("default_name", callback.from_user.first_name)

    await state.update_data(name=default_name)
    await state.set_state(CheckoutStates.waiting_phone)

    text = """
📝 <b>Оформление заказа</b>

<b>Шаг 2/4:</b> Введите ваш номер телефона

Формат: +7XXXXXXXXXX или 8XXXXXXXXXX
"""

    await callback.message.edit_text(text, parse_mode="HTML")
    await callback.answer()


@router.message(CheckoutStates.waiting_name)
async def process_name(message: Message, state: FSMContext):
    """Process customer name"""
    name = message.text.strip()

    if len(name) < 2:
        await message.answer("❌ Имя слишком короткое. Пожалуйста, введите корректное имя.")
        return

    await state.update_data(name=name)
    await state.set_state(CheckoutStates.waiting_phone)

    text = """
📝 <b>Оформление заказа</b>

<b>Шаг 2/4:</b> Введите ваш номер телефона

Формат: +7XXXXXXXXXX или 8XXXXXXXXXX
"""

    await message.answer(text, parse_mode="HTML")


@router.message(CheckoutStates.waiting_phone)
async def process_phone(message: Message, state: FSMContext, db: AsyncSession):
    """Process customer phone"""
    phone = message.text.strip()

    # Simple phone validation
    phone_digits = ''.join(filter(str.isdigit, phone))

    if len(phone_digits) < 10:
        await message.answer("❌ Неверный формат телефона. Пожалуйста, введите корректный номер.")
        return

    await state.update_data(phone=phone)

    # Save phone to user profile
    await user_service.update_phone(db, message.from_user.id, phone)

    await state.set_state(CheckoutStates.waiting_email)

    text = """
📝 <b>Оформление заказа</b>

<b>Шаг 3/4:</b> Введите ваш email (необязательно)

Email будет использован для отправки информации о заказе.
"""

    await message.answer(
        text,
        reply_markup=skip_keyboard("skip_email"),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "skip_email", CheckoutStates.waiting_email)
async def skip_email(callback: CallbackQuery, state: FSMContext):
    """Skip email input"""
    await state.update_data(email=None)
    await state.set_state(CheckoutStates.waiting_address)

    text = """
📝 <b>Оформление заказа</b>

<b>Шаг 4/4:</b> Введите адрес доставки

Укажите полный адрес с индексом, городом, улицей и номером дома/квартиры.
"""

    await callback.message.edit_text(
        text,
        reply_markup=skip_keyboard("skip_address"),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(CheckoutStates.waiting_email)
async def process_email(message: Message, state: FSMContext, db: AsyncSession):
    """Process customer email"""
    email = message.text.strip()

    # Simple email validation
    if '@' not in email or '.' not in email:
        await message.answer("❌ Неверный формат email. Пожалуйста, введите корректный email или пропустите этот шаг.")
        return

    await state.update_data(email=email)

    # Save email to user profile
    await user_service.update_email(db, message.from_user.id, email)

    await state.set_state(CheckoutStates.waiting_address)

    text = """
📝 <b>Оформление заказа</b>

<b>Шаг 4/4:</b> Введите адрес доставки

Укажите полный адрес с индексом, городом, улицей и номером дома/квартиры.
"""

    await message.answer(
        text,
        reply_markup=skip_keyboard("skip_address"),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "skip_address", CheckoutStates.waiting_address)
async def skip_address(callback: CallbackQuery, state: FSMContext):
    """Skip address (pickup)"""
    await state.update_data(address="Самовывоз")
    await show_order_confirmation(callback.message, state)
    await callback.answer()


@router.message(CheckoutStates.waiting_address)
async def process_address(message: Message, state: FSMContext):
    """Process delivery address"""
    address = message.text.strip()

    if len(address) < 10:
        await message.answer("❌ Адрес слишком короткий. Пожалуйста, укажите полный адрес.")
        return

    await state.update_data(address=address)
    await show_order_confirmation(message, state)


async def show_order_confirmation(message: Message, state: FSMContext):
    """Show order confirmation"""
    data = await state.get_data()
    user_id = message.from_user.id if hasattr(message, 'from_user') else message.chat.id

    # Get cart
    cart = await cart_service.get_cart(user_id)

    # Build order summary
    items_text = []
    for item in cart["items"]:
        product = item["product"]
        items_text.append(
            f"• {product['name']}\n"
            f"  {format_price(product['price'])} × {item['quantity']} = {format_price(item['subtotal'])}"
        )

    text = f"""
✅ <b>Подтверждение заказа</b>

<b>Ваши данные:</b>
👤 Имя: {data.get('name', 'Не указано')}
📞 Телефон: {data.get('phone', 'Не указан')}
📧 Email: {data.get('email', 'Не указан')}
📍 Адрес: {data.get('address', 'Самовывоз')}

<b>Товары:</b>
{chr(10).join(items_text)}

━━━━━━━━━━━━━━━━━
💰 <b>Итого: {format_price(cart['total'])}</b>

Подтвердите заказ для перехода к оплате.
"""

    await state.set_state(CheckoutStates.confirm)

    await message.answer(
        text,
        reply_markup=checkout_confirm_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "edit_order", CheckoutStates.confirm)
async def edit_order(callback: CallbackQuery, state: FSMContext):
    """Go back to edit order details"""
    await state.set_state(CheckoutStates.waiting_name)

    text = """
📝 <b>Редактирование заказа</b>

Введите ваше имя:
"""

    await callback.message.edit_text(text, parse_mode="HTML")
    await callback.answer()


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
