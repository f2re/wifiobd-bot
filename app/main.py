"""
Main entry point for VK bot
"""
import asyncio
import sys

from vkbottle.bot import Bot
from vkbottle import API

from app.bot import bot, api, labeler
from app.database import init_db
from app.services.cart import cart_service
from app.handlers import register_handlers
from app.utils.logger import get_logger
from config import settings

logger = get_logger(__name__)


async def on_startup():
    """Actions to perform on bot startup"""
    logger.info("VK Bot is starting up...")

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

    # Get group info
    try:
        group_info = await api.groups.get_by_id(group_ids=[settings.VK_GROUP_ID])
        if group_info:
            logger.info(f"Connected to VK Group: {group_info[0].name} (ID: {group_info[0].id})")
    except Exception as e:
        logger.warning(f"Could not fetch group info: {e}")

    logger.info("VK Bot startup completed successfully")


async def on_shutdown():
    """Actions to perform on bot shutdown"""
    logger.info("VK Bot is shutting down...")

    # Close Redis connection
    try:
        await cart_service.close_redis()
        logger.info("Redis connection closed")
    except Exception as e:
        logger.error(f"Error closing Redis: {e}")

    logger.info("VK Bot shutdown completed")


async def main():
    """Main function to run the VK bot"""
    try:
        # Register handlers
        register_handlers(bot)
        logger.info("Handlers registered")

        # Run startup actions
        await on_startup()

        # Start bot
        logger.info("Starting VK bot polling...")
        logger.info(f"VK Bot is running for group ID: {settings.VK_GROUP_ID}")

        try:
            await bot.run_polling()
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
