"""
Text formatting utilities for Telegram messages
"""
from typing import List, Dict, Any
from datetime import datetime


def format_price(price: float) -> str:
    """Format price with currency symbol"""
    return f"{price:,.2f}₽"


def format_date(dt: datetime) -> str:
    """Format datetime to readable string"""
    return dt.strftime("%d.%m.%Y %H:%M")


def format_product_name(name: str, max_length: int = 40) -> str:
    """Truncate product name if too long"""
    if len(name) <= max_length:
        return name
    return name[:max_length - 3] + "..."


def format_cart_item(item: Dict[str, Any]) -> str:
    """Format cart item for display"""
    product = item["product"]
    quantity = item["quantity"]
    subtotal = item["subtotal"]

    return (
        f"• {product.name}\n"
        f"  {format_price(product.price)} × {quantity} = {format_price(subtotal)}"
    )


def format_cart_summary(cart: Dict[str, Any]) -> str:
    """Format entire cart for display"""
    if not cart["items"]:
        return "🛒 <b>Ваша корзина пуста</b>"

    items_text = "\n\n".join([format_cart_item(item) for item in cart["items"]])
    total = cart["total"]

    return (
        f"🛒 <b>Ваша корзина:</b>\n\n"
        f"{items_text}\n\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"💰 <b>Итого: {format_price(total)}</b>"
    )


def format_order_items(items: List[Dict[str, Any]]) -> str:
    """Format order items for display"""
    result = []
    for item in items:
        result.append(
            f"• {item['name']}\n"
            f"  {format_price(item['price'])} × {item['quantity']} = {format_price(item['price'] * item['quantity'])}"
        )
    return "\n".join(result)


def format_order_summary(order) -> str:
    """Format complete order summary"""
    return f"""
📦 <b>Заказ #{order.id}</b>

👤 <b>Покупатель:</b> {order.customer_name}
📞 <b>Телефон:</b> {order.customer_phone}
📧 <b>Email:</b> {order.customer_email or 'Не указан'}

📍 <b>Адрес доставки:</b>
{order.delivery_address or 'Не указан'}

💬 <b>Комментарий:</b>
{order.delivery_comment or 'Нет комментариев'}

<b>Товары:</b>
{format_order_items(order.items)}

━━━━━━━━━━━━━━━━━
💰 <b>Итого: {format_price(order.amount)}</b>

📅 <b>Дата создания:</b> {format_date(order.created_at)}
📊 <b>Статус:</b> {get_status_emoji(order.status)} {get_status_text(order.status)}
"""


def get_status_emoji(status: str) -> str:
    """Get emoji for order status"""
    status_emojis = {
        "pending": "⏳",
        "paid": "✅",
        "cancelled": "❌",
        "refunded": "💸",
        "completed": "🎉"
    }
    return status_emojis.get(status, "❓")


def get_status_text(status: str) -> str:
    """Get Russian text for order status"""
    status_texts = {
        "pending": "Ожидает оплаты",
        "paid": "Оплачен",
        "cancelled": "Отменен",
        "refunded": "Возврат средств",
        "completed": "Выполнен"
    }
    return status_texts.get(status, "Неизвестно")


def escape_markdown(text: str) -> str:
    """Escape special characters for Telegram Markdown"""
    escape_chars = '_*[]()~`>#+-=|{}.!'
    return ''.join(['\\' + char if char in escape_chars else char for char in text])


def format_product_card(product, description_length: int = 300) -> str:
    """Format product details card"""
    # Handle both dict and object access
    if isinstance(product, dict):
        desc = product.get('description') or "Описание отсутствует"
        if len(desc) > description_length:
            desc = desc[:description_length] + "..."

        quantity = product.get('quantity', 0)
        stock_text = "В наличии" if quantity > 0 else "Нет в наличии"
        stock_emoji = "✅" if quantity > 0 else "❌"

        return f"""
<b>{product.get('name', 'Без названия')}</b>

{desc}

💰 <b>Цена:</b> {format_price(product.get('price', 0))}
📦 <b>Наличие:</b> {stock_emoji} {stock_text}
🏷 <b>Артикул:</b> {product.get('model', 'Н/Д')}
"""
    else:
        # Object attribute access (fallback for compatibility)
        desc = product.description or "Описание отсутствует"
        if len(desc) > description_length:
            desc = desc[:description_length] + "..."

        stock_text = "В наличии" if product.quantity > 0 else "Нет в наличии"
        stock_emoji = "✅" if product.quantity > 0 else "❌"

        return f"""
<b>{product.name}</b>

{desc}

💰 <b>Цена:</b> {format_price(product.price)}
📦 <b>Наличие:</b> {stock_emoji} {stock_text}
🏷 <b>Артикул:</b> {product.model}
"""


def breadcrumbs(path: List[str]) -> str:
    """Create breadcrumb navigation"""
    return " › ".join(path)
