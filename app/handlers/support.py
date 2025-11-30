"""
Support ticket system handlers for VK bot
"""
from vkbottle.bot import Bot, Message
from app.keyboards.inline import VKKeyboards
from app.utils.logger import get_logger
from config import settings

logger = get_logger(__name__)


def register_handlers(bot: Bot):
    """Register support handlers"""

    @bot.on.message(text=["💬 Поддержка", "💬 поддержка", "Поддержка", "поддержка"])
    async def support_handler(message: Message):
        """Show support information"""
        try:
            text = """
💬 <b>Служба поддержки WifiOBD</b>

Если у вас возникли вопросы или проблемы, свяжитесь с нами:

📧 Email: support@wifiobd.ru
📱 Телефон: +7 (XXX) XXX-XX-XX

🕐 Время работы: Пн-Пт 9:00-18:00 МСК

Вы также можете написать ваш вопрос прямо здесь, и мы ответим в ближайшее время.
"""

            await message.answer(text, keyboard=VKKeyboards.main_menu())

        except Exception as e:
            logger.error(f"Error in support handler: {e}", exc_info=True)
            await message.answer("❌ Произошла ошибка")

    @bot.on.message(payload={'action': 'support'})
    async def support_callback(message: Message):
        """Show support from callback"""
        await support_handler(message)

    logger.info("Support handlers registered")
