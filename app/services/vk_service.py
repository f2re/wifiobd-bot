"""
VK API Service - photo upload, attachments, carousels, user info
"""
from typing import List, Optional, Dict, Any
import aiohttp
import io
from vkbottle import API
from vkbottle.bot import Message

from app.bot import api
from app.utils.logger import get_logger
from config import settings

logger = get_logger(__name__)


class VKPhotoService:
    """Service for VK photo upload operations"""

    def __init__(self, api_instance: API):
        self.api = api_instance
        self.group_id = settings.VK_GROUP_ID

    async def upload_photo(self, image_url: str) -> Optional[str]:
        """
        Upload photo from URL to VK and return attachment string

        Args:
            image_url: URL of the image to upload

        Returns:
            Attachment string like 'photo-123456_789012' or None if failed
        """
        try:
            # Step 1: Get upload server
            upload_server_response = await self.api.photos.get_wall_upload_server(
                group_id=self.group_id
            )
            upload_url = upload_server_response.upload_url

            # Step 2: Download image from URL
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as resp:
                    if resp.status != 200:
                        logger.error(f"Failed to download image from {image_url}: status {resp.status}")
                        return None

                    image_data = await resp.read()

            # Step 3: Upload image to VK server
            form_data = aiohttp.FormData()
            form_data.add_field('photo', io.BytesIO(image_data), filename='photo.jpg', content_type='image/jpeg')

            async with aiohttp.ClientSession() as session:
                async with session.post(upload_url, data=form_data) as resp:
                    upload_result = await resp.json()

            if not upload_result.get('photo'):
                logger.error(f"Failed to upload photo to VK: {upload_result}")
                return None

            # Step 4: Save uploaded photo
            save_result = await self.api.photos.save_wall_photo(
                group_id=self.group_id,
                photo=upload_result['photo'],
                server=upload_result['server'],
                hash=upload_result['hash']
            )

            if not save_result:
                logger.error("Failed to save photo on VK")
                return None

            photo = save_result[0]
            attachment = f"photo{photo.owner_id}_{photo.id}"

            logger.info(f"Successfully uploaded photo: {attachment}")
            return attachment

        except Exception as e:
            logger.error(f"Error uploading photo from {image_url}: {e}", exc_info=True)
            return None

    async def upload_message_photo(self, image_url: str, peer_id: int) -> Optional[str]:
        """
        Upload photo for messages (different API endpoint)

        Args:
            image_url: URL of the image to upload
            peer_id: Peer ID for the conversation

        Returns:
            Attachment string or None if failed
        """
        try:
            # Get upload server for messages
            upload_server_response = await self.api.photos.get_messages_upload_server(
                peer_id=peer_id
            )
            upload_url = upload_server_response.upload_url

            # Download image
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as resp:
                    if resp.status != 200:
                        logger.error(f"Failed to download image: status {resp.status}")
                        return None
                    image_data = await resp.read()

            # Upload to VK
            form_data = aiohttp.FormData()
            form_data.add_field('photo', io.BytesIO(image_data), filename='photo.jpg', content_type='image/jpeg')

            async with aiohttp.ClientSession() as session:
                async with session.post(upload_url, data=form_data) as resp:
                    upload_result = await resp.json()

            # Save photo
            save_result = await self.api.photos.save_messages_photo(
                photo=upload_result['photo'],
                server=upload_result['server'],
                hash=upload_result['hash']
            )

            if not save_result:
                return None

            photo = save_result[0]
            attachment = f"photo{photo.owner_id}_{photo.id}"

            logger.info(f"Successfully uploaded message photo: {attachment}")
            return attachment

        except Exception as e:
            logger.error(f"Error uploading message photo: {e}", exc_info=True)
            return None


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

    async def create_product_carousel(
        self,
        products: List[Dict[str, Any]],
        peer_id: int
    ) -> Optional[str]:
        """Create product carousel template"""
        try:
            # VK carousel implementation
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


# Create global instances
vk_service = VKService(api)
vk_photo_service = VKPhotoService(api)
