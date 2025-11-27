"""
Throttling middleware for anti-spam
"""
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from cachetools import TTLCache

from config import settings


class ThrottlingMiddleware(BaseMiddleware):
    """
    Middleware to prevent spam by limiting user actions
    """

    def __init__(self, throttle_time: float = None):
        """
        Args:
            throttle_time: Time in seconds between allowed actions
        """
        self.throttle_time = throttle_time or settings.THROTTLE_TIME
        self.cache = TTLCache(maxsize=10000, ttl=self.throttle_time)

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        """Process event with throttling check"""

        user_id = event.from_user.id

        if user_id in self.cache:
            # User is throttled
            if isinstance(event, CallbackQuery):
                await event.answer(
                    "⏳ Пожалуйста, подождите немного перед следующим действием",
                    show_alert=False
                )
            return

        # Mark user as active
        self.cache[user_id] = True

        # Continue processing
        return await handler(event, data)
