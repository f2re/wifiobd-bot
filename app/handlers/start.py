"""
Start command and main menu handlers
"""
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy.ext.asyncio import AsyncSession

from app.keyboards.inline import main_menu_keyboard, cart_keyboard, back_to_main_menu_keyboard
from app.services.user import user_service
from app.services.cart import cart_service
from app.utils.logger import get_logger
from app.utils.formatting import format_cart_summary

logger = get_logger(__name__)

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, db: AsyncSession, state: FSMContext):
    """Handle /start command"""
    try:
        # Clear any active state
        await state.clear()

        # Get or create user
        user = await user_service.get_or_create_user(
            db=db,
            user_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name
        )

        welcome_text = f"""
👋 <b>Добро пожаловать в WifiOBD!</b>

Здравствуйте, {user.first_name}!

Мы рады приветствовать вас в нашем магазине автомобильной диагностики.

🛍 <b>Каталог</b> - просмотр товаров
🛒 <b>Корзина</b> - ваша корзина покупок
📦 <b>Мои заказы</b> - история заказов
💬 <b>Поддержка</b> - связаться с нами

Выберите раздел:
"""

        await message.answer(
            welcome_text,
            reply_markup=main_menu_keyboard(),
            parse_mode="HTML"
        )

        logger.info(f"User {message.from_user.id} started the bot")

    except Exception as e:
        logger.error(f"Error in start handler: {e}")
        await message.answer(
            "Произошла ошибка. Пожалуйста, попробуйте позже.",
            reply_markup=main_menu_keyboard()
        )


@router.callback_query(F.data == "start")
async def callback_start(callback: CallbackQuery, db: AsyncSession, state: FSMContext):
    """Handle main menu callback"""
    try:
        # Clear any active state
        await state.clear()

        # Get user info
        user = await user_service.get_or_create_user(
            db=db,
            user_id=callback.from_user.id,
            username=callback.from_user.username,
            first_name=callback.from_user.first_name,
            last_name=callback.from_user.last_name
        )

        welcome_text = f"""
🏠 <b>Главное меню</b>

Здравствуйте, {user.first_name}!

Выберите раздел:
"""

        # Check if current message has photo
        has_photo = callback.message.photo is not None and len(callback.message.photo) > 0

        if has_photo:
            # Delete photo message and send text
            await callback.message.delete()
            await callback.message.answer(
                welcome_text,
                reply_markup=main_menu_keyboard(),
                parse_mode="HTML"
            )
        else:
            try:
                await callback.message.edit_text(
                    welcome_text,
                    reply_markup=main_menu_keyboard(),
                    parse_mode="HTML"
                )
            except TelegramBadRequest as e:
                if "message is not modified" in str(e):
                    pass
                else:
                    raise

        await callback.answer()

    except Exception as e:
        logger.error(f"Error in main menu callback: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command"""
    help_text = """
📖 <b>Справка по боту</b>

<b>Команды:</b>
/start - Главное меню
/cart - Открыть корзину
/help - Эта справка
/admin - Админ-панель (только для администраторов)

<b>Разделы:</b>
🛍 <b>Каталог</b> - просмотр категорий и товаров
🛒 <b>Корзина</b> - управление корзиной
📦 <b>Мои заказы</b> - просмотр истории заказов
💬 <b>Поддержка</b> - обратиться в службу поддержки

<b>Оплата:</b>
Мы принимаем оплату через ЮMoney (банковские карты).

<b>Контакты:</b>
🌐 Сайт: https://wifiobd.ru
📧 Email: support@wifiobd.ru

По всем вопросам обращайтесь в раздел "Поддержка".
"""

    await message.answer(
        help_text,
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML"
    )


@router.message(Command("cart"))
async def cmd_cart(message: Message):
    """Handle /cart command - quick access to shopping cart"""
    try:
        user_id = message.from_user.id

        # Get cart
        cart = await cart_service.get_cart(user_id)

        if not cart["items"]:
            text = "🛒 <b>Ваша корзина пуста</b>\n\nДобавьте товары из каталога."
            keyboard = back_to_main_menu_keyboard()
        else:
            text = format_cart_summary(cart)
            keyboard = cart_keyboard(has_items=True)

        await message.answer(
            text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )

    except Exception as e:
        logger.error(f"Error in /cart command: {e}")
        await message.answer(
            "Произошла ошибка при загрузке корзины",
            reply_markup=main_menu_keyboard()
        )


@router.callback_query(F.data == "noop")
async def callback_noop(callback: CallbackQuery):
    """Handle no-op callbacks (e.g., page indicators)"""
    await callback.answer()
