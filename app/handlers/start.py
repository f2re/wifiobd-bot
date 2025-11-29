"""
Start handler for VK bot - main menu and help
"""
from vkbottle.bot import Bot, Message
from vkbottle import Keyboard, KeyboardButtonColor, Text

from app.keyboards.inline import VKKeyboards
from app.services.user import user_service
from app.utils.logger import get_logger
from config import settings

logger = get_logger(__name__)


def register_handlers(bot: Bot):
    """Register start handlers"""

    @bot.on.message(text=["Начать", "начать", "start", "/start"])
    async def start_handler(message: Message):
        """Handle start command"""
        try:
            # Get or create user
            user = await user_service.get_or_create_user(
                vk_id=message.from_id,
                first_name=message.from_id  # Will be updated from VK API
            )

            welcome_text = (
                f"👋 Добро пожаловать в магазин WifiOBD!\n\n"
                f"Здесь вы можете:\n"
                f"🛍 Просмотреть каталог товаров\n"
                f"🛒 Добавить товары в корзину\n"
                f"💳 Оплатить заказ онлайн\n"
                f"📦 Отслеживать статус заказа\n\n"
                f"Выберите действие:"
            )

            await message.answer(
                message=welcome_text,
                keyboard=VKKeyboards.main_menu()
            )

            logger.info(f"User {message.from_id} started the bot")

        except Exception as e:
            logger.error(f"Error in start handler: {e}", exc_info=True)
            await message.answer(
                "❌ Произошла ошибка. Попробуйте позже.",
                keyboard=VKKeyboards.main_menu()
            )

    @bot.on.message(text=["Помощь", "помощь", "ℹ️ Помощь", "/help"])
    async def help_handler(message: Message):
        """Handle help command"""
        try:
            help_text = (
                "📖 <b>Справка по боту WifiOBD</b>\n\n"
                "<b>Основные команды:</b>\n"
                "🛍 <b>Каталог</b> - просмотр товаров\n"
                "🛒 <b>Корзина</b> - управление корзиной\n"
                "📦 <b>Мои заказы</b> - история покупок\n"
                "💬 <b>Поддержка</b> - связь с нами\n\n"
                "<b>Оплата:</b>\n"
                "Принимаем оплату банковскими картами через YooKassa.\n"
                "Все платежи защищены и безопасны.\n\n"
                "<b>Доставка:</b>\n"
                "Доставка по всей России транспортными компаниями.\n\n"
                "<b>Контакты:</b>\n"
                f"🌐 Сайт: {settings.OPENCART_URL}\n"
                "📧 Email: support@wifiobd.ru\n\n"
                "Если у вас остались вопросы, нажмите 💬 Поддержка"
            )

            await message.answer(
                message=help_text,
                keyboard=VKKeyboards.main_menu()
            )

        except Exception as e:
            logger.error(f"Error in help handler: {e}", exc_info=True)
            await message.answer(
                "❌ Произошла ошибка. Попробуйте позже.",
                keyboard=VKKeyboards.main_menu()
            )

    @bot.on.message(text="🔙 Главное меню")
    async def main_menu_handler(message: Message):
        """Return to main menu"""
        try:
            await message.answer(
                message="Главное меню:",
                keyboard=VKKeyboards.main_menu()
            )
        except Exception as e:
            logger.error(f"Error in main menu handler: {e}", exc_info=True)

    # Admin command
    @bot.on.message(text=["Админ", "админ", "admin", "/admin"])
    async def admin_handler(message: Message):
        """Handle admin command"""
        try:
            # Check if user is admin
            if message.from_id not in settings.ADMIN_IDS:
                await message.answer("❌ У вас нет прав администратора.")
                return

            admin_text = (
                "👨‍💼 <b>Панель администратора</b>\n\n"
                "Выберите действие:"
            )

            await message.answer(
                message=admin_text,
                keyboard=VKKeyboards.admin_menu()
            )

            logger.info(f"Admin {message.from_id} accessed admin panel")

        except Exception as e:
            logger.error(f"Error in admin handler: {e}", exc_info=True)
            await message.answer("❌ Произошла ошибка.")

    logger.info("Start handlers registered")
