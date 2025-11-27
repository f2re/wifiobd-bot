"""
Bot instance initialization
"""
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Initialize bot
bot = Bot(
    token=settings.BOT_TOKEN,
    default=DefaultBotProperties(
        parse_mode=ParseMode.HTML
    )
)

# Initialize dispatcher
dp = Dispatcher()

logger.info("Bot and Dispatcher initialized")
