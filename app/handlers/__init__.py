"""VK Bot Handlers module"""
from vkbottle.bot import Bot

from . import start
from . import catalog
from . import cart
from . import checkout
from . import payment
from . import admin
from . import support


def register_handlers(bot: Bot):
    """Register all bot handlers"""
    # Register handlers for each module
    start.register_handlers(bot)
    catalog.register_handlers(bot)
    cart.register_handlers(bot)
    checkout.register_handlers(bot)
    payment.register_handlers(bot)
    admin.register_handlers(bot)
    support.register_handlers(bot)
