"""
Main entry point for the bot
"""
import asyncio
import sys
from contextlib import asynccontextmanager

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from app.bot import bot, dp
from app.database import init_db
from app.services.cart import cart_service
from app.middlewares import ThrottlingMiddleware, DatabaseMiddleware
from app.handlers import routers
from app.utils.logger import get_logger
from config import settings

logger = get_logger(__name__)


async def on_startup():
    """Actions to perform on bot startup"""
    logger.info("Bot is starting up...")

    # Initialize database
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

    # Initialize Redis for cart service
    try:
        await cart_service.init_redis()
        logger.info("Redis initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Redis: {e}")
        raise

    logger.info("Bot startup completed successfully")


async def on_shutdown():
    """Actions to perform on bot shutdown"""
    logger.info("Bot is shutting down...")

    # Close Redis connection
    try:
        await cart_service.close_redis()
        logger.info("Redis connection closed")
    except Exception as e:
        logger.error(f"Error closing Redis: {e}")

    # Close bot session
    await bot.session.close()

    logger.info("Bot shutdown completed")


async def main():
    """Main function to run the bot"""
    try:
        # Register middlewares
        dp.message.middleware(DatabaseMiddleware())
        dp.callback_query.middleware(DatabaseMiddleware())
        dp.message.middleware(ThrottlingMiddleware())
        dp.callback_query.middleware(ThrottlingMiddleware())

        logger.info("Middlewares registered")

        # Register routers
        for router in routers:
            dp.include_router(router)

        logger.info(f"Registered {len(routers)} routers")

        # Run startup actions
        await on_startup()

        # Start polling
        logger.info("Starting bot polling...")
        logger.info(f"Bot @{(await bot.get_me()).username} is running!")

        try:
            await dp.start_polling(
                bot,
                allowed_updates=dp.resolve_used_update_types(),
                drop_pending_updates=True
            )
        finally:
            await on_shutdown()

    except KeyboardInterrupt:
        logger.info("Bot stopped by user (Ctrl+C)")
    except Exception as e:
        logger.error(f"Fatal error in main: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)
