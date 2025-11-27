"""
Inline keyboard builders
"""
from typing import List, Dict, Any
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Main menu keyboard"""
    builder = InlineKeyboardBuilder()

    builder.button(text="🛍 Каталог", callback_data="catalog")
    builder.button(text="🛒 Корзина", callback_data="cart")
    builder.button(text="📦 Мои заказы", callback_data="my_orders")
    builder.button(text="💬 Поддержка", callback_data="support")

    builder.adjust(2)
    return builder.as_markup()


def back_to_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Simple back to main menu button"""
    builder = InlineKeyboardBuilder()
    builder.button(text="🏠 Главное меню", callback_data="start")
    return builder.as_markup()


def categories_keyboard(categories: List[Dict[str, Any]], parent_id: int = 0) -> InlineKeyboardMarkup:
    """
    Keyboard for displaying categories

    Args:
        categories: List of category dicts
        parent_id: Parent category ID (for back button)
    """
    builder = InlineKeyboardBuilder()

    for category in categories:
        builder.button(
            text=f"📁 {category['name']}",
            callback_data=f"cat:{category['category_id']}"
        )

    builder.adjust(2)

    # Navigation buttons
    if parent_id > 0:
        builder.row(InlineKeyboardButton(
            text="🔙 Назад",
            callback_data=f"cat:{parent_id}"
        ))
    else:
        builder.row(InlineKeyboardButton(
            text="🏠 Главное меню",
            callback_data="start"
        ))

    return builder.as_markup()


def products_keyboard(
    products: List[Dict[str, Any]],
    category_id: int,
    page: int = 0,
    has_next: bool = False,
    parent_id: int = 0
) -> InlineKeyboardMarkup:
    """
    Keyboard for displaying products with pagination

    Args:
        products: List of product dicts
        category_id: Category ID
        page: Current page
        has_next: Whether there's a next page
        parent_id: Parent category ID for back button
    """
    builder = InlineKeyboardBuilder()

    for product in products:
        price_text = f"{product['price']:.2f}₽"
        builder.button(
            text=f"{product['name']} - {price_text}",
            callback_data=f"prod:{product['product_id']}"
        )

    builder.adjust(1)

    # Pagination
    pagination_buttons = []
    if page > 0:
        pagination_buttons.append(InlineKeyboardButton(
            text="◀️",
            callback_data=f"catpage:{category_id}:{page - 1}"
        ))

    pagination_buttons.append(InlineKeyboardButton(
        text=f"{page + 1}",
        callback_data="noop"
    ))

    if has_next:
        pagination_buttons.append(InlineKeyboardButton(
            text="▶️",
            callback_data=f"catpage:{category_id}:{page + 1}"
        ))

    if pagination_buttons:
        builder.row(*pagination_buttons)

    # Back button - navigate to parent category or catalog root
    if parent_id > 0:
        builder.row(InlineKeyboardButton(
            text="🔙 Назад к категориям",
            callback_data=f"cat:{parent_id}"
        ))
    else:
        builder.row(InlineKeyboardButton(
            text="🔙 Назад к категориям",
            callback_data="catalog"
        ))

    return builder.as_markup()


def product_card_keyboard(product_id: int, category_id: int, in_stock: bool = True) -> InlineKeyboardMarkup:
    """Keyboard for product card"""
    builder = InlineKeyboardBuilder()

    if in_stock:
        builder.button(
            text="➕ В корзину",
            callback_data=f"addcart:{product_id}"
        )

    builder.button(
        text="🔙 Назад к товарам",
        callback_data=f"cat:{category_id}"
    )

    builder.adjust(1)
    return builder.as_markup()


def cart_keyboard(has_items: bool = False) -> InlineKeyboardMarkup:
    """Keyboard for cart view"""
    builder = InlineKeyboardBuilder()

    if has_items:
        builder.button(text="✅ Оформить заказ", callback_data="checkout")
        builder.button(text="🗑 Очистить корзину", callback_data="clear_cart")

    builder.button(text="🛍 Продолжить покупки", callback_data="catalog")
    builder.button(text="🏠 Главное меню", callback_data="start")

    builder.adjust(1)
    return builder.as_markup()


def cart_item_keyboard(product_id: int, quantity: int) -> InlineKeyboardMarkup:
    """Keyboard for individual cart item"""
    builder = InlineKeyboardBuilder()

    builder.button(text="➖", callback_data=f"cart_dec:{product_id}")
    builder.button(text=f"{quantity}", callback_data="noop")
    builder.button(text="➕", callback_data=f"cart_inc:{product_id}")
    builder.row(InlineKeyboardButton(
        text="🗑 Удалить",
        callback_data=f"cart_remove:{product_id}"
    ))

    return builder.as_markup()


def checkout_confirm_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for order confirmation"""
    builder = InlineKeyboardBuilder()

    builder.button(text="✅ Подтвердить и оплатить", callback_data="confirm_order")
    builder.button(text="✏️ Изменить данные", callback_data="edit_order")
    builder.button(text="❌ Отменить", callback_data="cancel_order")

    builder.adjust(1)
    return builder.as_markup()


def payment_keyboard(order_id: int, payment_url: str) -> InlineKeyboardMarkup:
    """Keyboard for payment"""
    builder = InlineKeyboardBuilder()

    builder.button(
        text="💳 Оплатить",
        url=payment_url
    )
    builder.button(
        text="✅ Проверить оплату",
        callback_data=f"checkpay:{order_id}"
    )
    builder.button(
        text="❌ Отменить заказ",
        callback_data=f"cancelpay:{order_id}"
    )

    builder.adjust(1)
    return builder.as_markup()


def skip_keyboard(callback_data: str = "skip") -> InlineKeyboardMarkup:
    """Skip button keyboard"""
    builder = InlineKeyboardBuilder()
    builder.button(text="⏭ Пропустить", callback_data=callback_data)
    return builder.as_markup()


def admin_menu_keyboard() -> InlineKeyboardMarkup:
    """Admin panel main menu"""
    builder = InlineKeyboardBuilder()

    builder.button(text="📋 Заказы", callback_data="admin:orders")
    builder.button(text="💬 Обращения", callback_data="admin:tickets")
    builder.button(text="👥 Пользователи", callback_data="admin:users")
    builder.button(text="📊 Статистика", callback_data="admin:stats")
    builder.button(text="📢 Рассылка", callback_data="admin:broadcast")

    builder.adjust(2)
    return builder.as_markup()


def admin_order_keyboard(order_id: int, status: str, user_id: int) -> InlineKeyboardMarkup:
    """Keyboard for admin order management"""
    builder = InlineKeyboardBuilder()

    if status == "paid":
        builder.button(
            text="✅ Завершить заказ",
            callback_data=f"admin:complete:{order_id}"
        )
        builder.button(
            text="💸 Вернуть средства",
            callback_data=f"admin:refund:{order_id}"
        )

    if status == "pending":
        builder.button(
            text="❌ Отменить заказ",
            callback_data=f"admin:cancel:{order_id}"
        )

    builder.button(
        text="💬 Написать клиенту",
        callback_data=f"admin:msg:{user_id}"
    )
    builder.button(text="🔙 Назад", callback_data="admin:orders")

    builder.adjust(1)
    return builder.as_markup()


def admin_ticket_keyboard(ticket_id: int) -> InlineKeyboardMarkup:
    """Keyboard for support ticket"""
    builder = InlineKeyboardBuilder()

    builder.button(
        text="✏️ Ответить",
        callback_data=f"admin:reply:{ticket_id}"
    )
    builder.button(
        text="✅ Закрыть",
        callback_data=f"admin:close_ticket:{ticket_id}"
    )
    builder.button(text="🔙 Назад", callback_data="admin:tickets")

    builder.adjust(1)
    return builder.as_markup()
