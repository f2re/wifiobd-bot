"""Handlers module"""
from . import start
from . import catalog
from . import cart
from . import checkout
from . import payment
from . import admin
from . import support

# Export all routers
routers = [
    start.router,
    catalog.router,
    cart.router,
    checkout.router,
    payment.router,
    admin.router,
    support.router,
]
