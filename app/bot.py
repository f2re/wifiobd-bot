"""
VK Bot instance initialization
"""
from vkbottle.bot import Bot
from vkbottle import API, LoopWrapper
from vkbottle.dispatch.labeler import BotLabeler

from config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Initialize VK API
api = API(token=settings.VK_TOKEN)

# Initialize bot
bot = Bot(
    token=settings.VK_TOKEN,
    loop_wrapper=LoopWrapper()
)

# Initialize labeler for handlers
labeler = BotLabeler()

logger.info("VK Bot and API initialized")
