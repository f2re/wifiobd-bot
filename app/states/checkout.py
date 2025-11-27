"""
FSM states for checkout process
"""
from aiogram.fsm.state import State, StatesGroup


class CheckoutStates(StatesGroup):
    """States for order checkout process"""
    waiting_name = State()
    waiting_phone = State()
    waiting_email = State()
    waiting_address = State()
    waiting_comment = State()
    confirm = State()
