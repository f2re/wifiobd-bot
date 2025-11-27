"""
Pagination utilities for lists and catalogs
"""
from typing import List, Any, Tuple
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def paginate_items(items: List[Any], page: int, per_page: int) -> Tuple[List[Any], bool, bool]:
    """
    Paginate a list of items

    Args:
        items: List of items to paginate
        page: Current page number (0-indexed)
        per_page: Items per page

    Returns:
        Tuple of (paginated_items, has_prev, has_next)
    """
    start = page * per_page
    end = start + per_page

    paginated = items[start:end]
    has_prev = page > 0
    has_next = end < len(items)

    return paginated, has_prev, has_next


def create_pagination_buttons(
    page: int,
    has_prev: bool,
    has_next: bool,
    callback_prefix: str,
    total_pages: int = None
) -> List[InlineKeyboardButton]:
    """
    Create pagination navigation buttons

    Args:
        page: Current page number (0-indexed)
        has_prev: Whether there's a previous page
        has_next: Whether there's a next page
        callback_prefix: Prefix for callback data (e.g., "catpage:5")
        total_pages: Total number of pages (optional, for display)

    Returns:
        List of InlineKeyboardButton for pagination
    """
    buttons = []

    if has_prev:
        buttons.append(InlineKeyboardButton(
            text="◀️",
            callback_data=f"{callback_prefix}:{page - 1}"
        ))

    # Page indicator
    if total_pages:
        page_text = f"{page + 1}/{total_pages}"
    else:
        page_text = f"{page + 1}"

    buttons.append(InlineKeyboardButton(
        text=page_text,
        callback_data="noop"
    ))

    if has_next:
        buttons.append(InlineKeyboardButton(
            text="▶️",
            callback_data=f"{callback_prefix}:{page + 1}"
        ))

    return buttons


def add_pagination_to_keyboard(
    keyboard: InlineKeyboardBuilder,
    page: int,
    has_prev: bool,
    has_next: bool,
    callback_prefix: str,
    total_pages: int = None
):
    """
    Add pagination row to existing keyboard

    Args:
        keyboard: InlineKeyboardBuilder instance
        page: Current page number
        has_prev: Whether there's a previous page
        has_next: Whether there's a next page
        callback_prefix: Prefix for callback data
        total_pages: Total number of pages (optional)
    """
    pagination_buttons = create_pagination_buttons(
        page, has_prev, has_next, callback_prefix, total_pages
    )

    if pagination_buttons:
        keyboard.row(*pagination_buttons)


def calculate_total_pages(total_items: int, per_page: int) -> int:
    """Calculate total number of pages"""
    return (total_items + per_page - 1) // per_page
