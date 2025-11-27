"""
FSM states for admin operations
"""
from aiogram.fsm.state import State, StatesGroup


class AdminStates(StatesGroup):
    """States for admin operations"""
    waiting_message_to_user = State()
    waiting_broadcast_message = State()


class SupportStates(StatesGroup):
    """States for support ticket operations"""
    waiting_message = State()
    waiting_response = State()
