"""
Admin filter to restrict access to admin commands
"""
from aiogram.filters import Filter
from aiogram.types import Message, CallbackQuery

from config import settings


class IsAdmin(Filter):
    """Filter to check if user is admin"""

    async def __call__(self, event: Message | CallbackQuery) -> bool:
        """Check if user ID is in admin list"""
        return event.from_user.id in settings.ADMIN_IDS
