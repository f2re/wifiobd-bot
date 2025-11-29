"""
VK Carousel builder for products
"""
from typing import List, Dict, Any
from vkbottle import Keyboard, KeyboardButtonColor, Callback, OpenLink

from app.utils.logger import get_logger

logger = get_logger(__name__)


class CarouselBuilder:
    """Builder for VK product carousels"""

    @staticmethod
    def build_product_carousel(
        products: List[Dict[str, Any]],
        category_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Build carousel elements for products"""
        elements = []
        
        for product in products[:10]:  # VK carousel limit
            # Build product element
            element = {
                "title": product["name"][:80],  # VK title limit
                "description": product.get("description", "")[:220],  # VK description limit
                "photo_id": product.get("vk_photo_id"),  # VK photo attachment
                "buttons": [
                    {
                        "action": {
                            "type": "callback",
                            "label": "➕ В корзину",
                            "payload": {
                                "action": "add_to_cart",
                                "product_id": product["id"]
                            }
                        }
                    },
                    {
                        "action": {
                            "type": "callback",
                            "label": "📝 Подробнее",
                            "payload": {
                                "action": "view_product",
                                "product_id": product["id"]
                            }
                        }
                    }
                ]
            }
            
            # Add price if available
            if "price" in product:
                element["description"] = f"{product['price']} ₽\n{element['description']}"
            
            elements.append(element)
        
        logger.info(f"Built carousel with {len(elements)} products")
        return elements

    @staticmethod
    def build_category_carousel(
        categories: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Build carousel for categories"""
        elements = []
        
        for category in categories[:10]:
            element = {
                "title": category["name"][:80],
                "description": category.get("description", "Категория товаров")[:220],
                "photo_id": category.get("vk_photo_id"),
                "buttons": [
                    {
                        "action": {
                            "type": "callback",
                            "label": "👉 Перейти",
                            "payload": {
                                "action": "category",
                                "id": category["id"]
                            }
                        }
                    }
                ]
            }
            elements.append(element)
        
        return elements

    @staticmethod
    def format_carousel_message(
        text: str,
        elements: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Format carousel message for VK API"""
        return {
            "message": text,
            "template": {
                "type": "carousel",
                "elements": elements
            }
        }
