"""
Admin panel handlers for VK bot
"""
from vkbottle.bot import Bot, Message
from app.keyboards.inline import VKKeyboards
from app.utils.logger import get_logger
from config import settings

logger = get_logger(__name__)


def register_handlers(bot: Bot):
    """Register admin handlers"""

    @bot.on.message(text=["admin", "Admin", "ADMIN", "/admin"])
    async def admin_panel(message: Message):
        """Show admin panel"""
        try:
            # Check if user is admin
            if message.from_id not in settings.ADMIN_IDS:
                await message.answer("❌ У вас нет прав администратора.")
                return

            text = """
⚙️ <b>Админ-панель WifiOBD VK Bot</b>

Доступные команды:
• /stats - Статистика бота
• /users - Список пользователей
• /orders - Последние заказы
• /broadcast [текст] - Рассылка сообщения

Для просмотра детальной информации используйте команды выше.
"""

            await message.answer(text, keyboard=VKKeyboards.admin_menu())

            logger.info(f"Admin {message.from_id} accessed admin panel")

        except Exception as e:
            logger.error(f"Error in admin panel: {e}", exc_info=True)
            await message.answer("❌ Произошла ошибка")

    @bot.on.message(text=["/stats", "stats"])
    async def admin_stats(message: Message):
        """Show statistics"""
        try:
            if message.from_id not in settings.ADMIN_IDS:
                return

            # TODO: Implement real stats from database
            text = """
📊 <b>Статистика бота</b>

👥 Всего пользователей: N/A
📦 Всего заказов: N/A
💰 Общая выручка: N/A

Статистика в разработке.
"""

            await message.answer(text, keyboard=VKKeyboards.admin_menu())

        except Exception as e:
            logger.error(f"Error showing stats: {e}", exc_info=True)

    logger.info("Admin handlers registered")
