"""
VK-specific helper functions
"""
from typing import Optional, Dict, Any, List
import json
import re

from app.utils.logger import get_logger

logger = get_logger(__name__)


def parse_callback_data(payload: str) -> Optional[Dict[str, Any]]:
    """Parse callback button payload"""
    try:
        if isinstance(payload, str):
            return json.loads(payload)
        return payload
    except Exception as e:
        logger.error(f"Error parsing callback data: {e}")
        return None


def extract_command_args(text: str) -> List[str]:
    """Extract command arguments from message text"""
    # Split by spaces but preserve quoted strings
    pattern = r'"([^"]*)"|\S+'
    matches = re.findall(pattern, text)
    return [m[0] if m[0] else m[1] for m in matches]


def format_price(price: float) -> str:
    """Format price for display"""
    return f"{price:,.2f} ₽".replace(",", " ")


def truncate_text(text: str, max_length: int = 4096, suffix: str = "...") -> str:
    """Truncate text to VK message limit"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def escape_html(text: str) -> str:
    """Escape HTML entities for VK messages"""
    replacements = {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def build_vk_attachment(attachment_type: str, owner_id: int, media_id: int) -> str:
    """Build VK attachment string"""
    return f"{attachment_type}{owner_id}_{media_id}"


def parse_vk_attachment(attachment: str) -> Optional[Dict[str, Any]]:
    """Parse VK attachment string"""
    try:
        match = re.match(r"(\w+)(-?\d+)_(\d+)", attachment)
        if match:
            return {
                "type": match.group(1),
                "owner_id": int(match.group(2)),
                "media_id": int(match.group(3))
            }
    except Exception as e:
        logger.error(f"Error parsing attachment: {e}")
    return None


def format_order_status(status: str) -> str:
    """Format order status with emoji"""
    status_map = {
        "pending": "⏳ Ожидает оплаты",
        "processing": "🔄 В обработке",
        "shipped": "🚚 Отправлен",
        "delivered": "✅ Доставлен",
        "cancelled": "❌ Отменен",
        "refunded": "💵 Возврат"
    }
    return status_map.get(status.lower(), status)


def format_payment_status(status: str) -> str:
    """Format payment status with emoji"""
    status_map = {
        "pending": "⏳ Ожидает оплаты",
        "succeeded": "✅ Оплачен",
        "canceled": "❌ Отменен",
        "waiting_for_capture": "⏳ Ожидание подтверждения"
    }
    return status_map.get(status.lower(), status)


def create_mention(user_id: int, name: str) -> str:
    """Create VK user mention"""
    return f"[id{user_id}|{name}]"


def validate_vk_user_id(user_id: int) -> bool:
    """Validate VK user ID"""
    # VK user IDs are positive integers
    # Group IDs are negative
    return isinstance(user_id, int) and user_id != 0


def get_vk_profile_url(user_id: int) -> str:
    """Get VK profile URL"""
    if user_id > 0:
        return f"https://vk.com/id{user_id}"
    else:
        return f"https://vk.com/club{abs(user_id)}"


def chunk_list(items: List[Any], chunk_size: int) -> List[List[Any]]:
    """Split list into chunks"""
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]


def format_datetime(dt: Any, format_str: str = "%d.%m.%Y %H:%M") -> str:
    """Format datetime for display"""
    try:
        if hasattr(dt, 'strftime'):
            return dt.strftime(format_str)
        return str(dt)
    except Exception:
        return str(dt)
