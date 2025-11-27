"""
Database session middleware
"""
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from app.database import SessionLocal


class DatabaseMiddleware(BaseMiddleware):
    """Middleware to provide database session to handlers"""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """Inject database session into handler data"""

        async with SessionLocal() as session:
            data["db"] = session
            return await handler(event, data)
