"""
Text formatting utilities for Telegram messages
"""
from typing import List, Dict, Any
from datetime import datetime
import re
import html


def clean_html(text: str) -> str:
    """Remove HTML tags and decode entities, safe for Telegram HTML parse_mode"""
    if not text:
        return ""

    # First, decode HTML entities BEFORE removing tags
    # This prevents double-decoding issues
    text = html.unescape(text)

    # Replace block-level tags with space to preserve word boundaries
    text = re.sub(r'</(p|div|h[1-6]|li|tr|td|th|br)>', ' ', text, flags=re.IGNORECASE)
    text = re.sub(r'<(br|hr)\s*/?>', ' ', text, flags=re.IGNORECASE)

    # Remove all remaining HTML tags
    text = re.sub(r'<[^>]+>', '', text)

    # Escape special HTML characters for Telegram
    # Telegram's HTML parse_mode requires escaping these characters if they appear in text
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')

    # Clean up extra whitespace and newlines
    text = re.sub(r'\s+', ' ', text).strip()

    return text


def smart_truncate(text: str, max_length: int = 300) -> tuple:
    """
    Truncate text at sentence or word boundary

    Returns:
        tuple: (truncated_text, was_truncated)
    """
    if len(text) <= max_length:
        return text, False

    # Try to truncate at sentence boundary (look ahead a bit to find complete sentence)
    search_text = text[:max_length + 100]
    sentences = re.split(r'([.!?]+)\s+', search_text)

    # Reconstruct sentences with their punctuation
    accumulated = ""
    for i in range(0, len(sentences) - 1, 2):
        sentence = sentences[i]
        punct = sentences[i + 1] if i + 1 < len(sentences) else ""
        if len(accumulated + sentence + punct) <= max_length:
            accumulated += sentence + punct + " "
        else:
            break

    if accumulated.strip():
        return accumulated.strip(), True

    # Fallback to word boundary if no sentence found
    truncated = text[:max_length].rsplit(' ', 1)[0]
    return truncated + '...', True


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

    # Handle both dict and object access for product
    if isinstance(product, dict):
        name = product.get("name", "Товар")
        price = product.get("price", 0)
    else:
        name = product.name
        price = product.price

    return (
        f"• {name}\n"
        f"  {format_price(price)} × {quantity} = {format_price(subtotal)}"
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


def format_product_card(product, description_length: int = 300, product_url: str = None) -> str:
    """Format product details card with HTML styling"""
    # Handle both dict and object access
    if isinstance(product, dict):
        name = product.get('name', 'Без названия')
        desc = product.get('description') or "Описание отсутствует"
        price = product.get('price', 0)
        quantity = product.get('quantity', 0)
        model = product.get('model', 'Н/Д')

        # Clean HTML tags and entities from description
        desc = clean_html(desc)

        # Smart truncation at sentence or word boundary
        desc, is_truncated = smart_truncate(desc, description_length)

        stock_text = "✅ В наличии" if quantity > 0 else "❌ Нет в наличии"

        # Build description with link if truncated
        description_html = f"<i>{desc}</i>"
        if is_truncated and product_url:
            description_html += f'\n\n<a href="{product_url}">📖 Читать полное описание →</a>'

        return f"""
<b>🛍 {name}</b>

{description_html}

━━━━━━━━━━━━━━━━━
💰 <b>Цена:</b> <code>{format_price(price)}</code>
📦 <b>Статус:</b> {stock_text}
🏷 <b>Артикул:</b> <code>{model}</code>
━━━━━━━━━━━━━━━━━
"""
    else:
        # Object attribute access (fallback for compatibility)
        name = product.name
        desc = product.description or "Описание отсутствует"
        price = product.price
        quantity = product.quantity
        model = product.model

        # Clean HTML tags and entities from description
        desc = clean_html(desc)

        # Smart truncation at sentence or word boundary
        desc, is_truncated = smart_truncate(desc, description_length)

        stock_text = "✅ В наличии" if quantity > 0 else "❌ Нет в наличии"

        # Build description with link if truncated
        description_html = f"<i>{desc}</i>"
        if is_truncated and product_url:
            description_html += f'\n\n<a href="{product_url}">📖 Читать полное описание →</a>'

        return f"""
<b>🛍 {name}</b>

{description_html}

━━━━━━━━━━━━━━━━━
💰 <b>Цена:</b> <code>{format_price(price)}</code>
📦 <b>Статус:</b> {stock_text}
🏷 <b>Артикул:</b> <code>{model}</code>
━━━━━━━━━━━━━━━━━
"""


def breadcrumbs(path: List[str]) -> str:
    """Create breadcrumb navigation"""
    return " › ".join(path)
