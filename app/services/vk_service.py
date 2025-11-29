"""
VK API Service - attachments, carousels, user info
"""
from typing import List, Optional, Dict, Any
from vkbottle import API
from vkbottle.bot import Message

from app.bot import api
from app.utils.logger import get_logger

logger = get_logger(__name__)


class VKService:
    """Service for VK API operations"""

    def __init__(self, api_instance: API):
        self.api = api_instance

    async def get_user_info(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user information from VK"""
        try:
            users = await self.api.users.get(user_ids=[user_id], fields=["photo_200"])
            if users:
                user = users[0]
                return {
                    "id": user.id,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "photo": getattr(user, "photo_200", None)
                }
        except Exception as e:
            logger.error(f"Error getting user info for {user_id}: {e}")
        return None

    async def upload_photo(self, peer_id: int, photo_path: str) -> Optional[str]:
        """Upload photo and get attachment string"""
        try:
            # Get upload server
            upload_server = await self.api.photos.get_messages_upload_server(
                peer_id=peer_id
            )

            # Upload photo (implementation depends on photo source)
            # This is a placeholder - actual implementation needed
            logger.info(f"Photo upload initiated for peer {peer_id}")
            return None

        except Exception as e:
            logger.error(f"Error uploading photo: {e}")
            return None

    async def create_product_carousel(
        self, 
        products: List[Dict[str, Any]],
        peer_id: int
    ) -> Optional[str]:
        """Create product carousel template"""
        try:
            # VK carousel implementation
            # This would create a carousel of products with images
            elements = []
            
            for product in products[:10]:  # VK limit
                element = {
                    "title": product["name"][:80],
                    "description": product.get("description", "")[:80],
                    "photo_id": product.get("photo_id"),
                    "buttons": [
                        {
                            "action": {
                                "type": "open_link",
                                "link": product.get("url", ""),
                                "label": "Подробнее"
                            }
                        }
                    ]
                }
                elements.append(element)

            logger.info(f"Created carousel with {len(elements)} products")
            return None  # Return carousel template

        except Exception as e:
            logger.error(f"Error creating carousel: {e}")
            return None

    async def send_location(self, peer_id: int, lat: float, long: float, title: str = "") -> bool:
        """Send location to user"""
        try:
            await self.api.messages.send(
                peer_id=peer_id,
                lat=lat,
                long=long,
                random_id=0,
                message=title or "📍 Местоположение"
            )
            return True
        except Exception as e:
            logger.error(f"Error sending location: {e}")
            return False

    async def get_conversation_members_count(self, peer_id: int) -> int:
        """Get count of conversation members"""
        try:
            response = await self.api.messages.get_conversation_members(
                peer_id=peer_id
            )
            return response.count if response else 0
        except Exception as e:
            logger.error(f"Error getting conversation members: {e}")
            return 0

    async def send_typing(self, peer_id: int) -> bool:
        """Send typing activity"""
        try:
            await self.api.messages.set_activity(
                peer_id=peer_id,
                type="typing"
            )
            return True
        except Exception as e:
            logger.error(f"Error sending typing: {e}")
            return False


# Create global instance
vk_service = VKService(api)
