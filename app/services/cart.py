"""
Shopping cart service using Redis for temporary storage
"""
from typing import List, Dict, Any, Optional
import json
import redis.asyncio as redis
from config import settings
from app.services.opencart import opencart_service
from app.utils.logger import get_logger

logger = get_logger(__name__)


class CartService:
    """Service for managing shopping carts in Redis"""

    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.expire_seconds = settings.CART_EXPIRE_DAYS * 24 * 3600

    async def init_redis(self):
        """Initialize Redis connection"""
        if not self.redis_client:
            self.redis_client = await redis.from_url(
                f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}",
                password=settings.REDIS_PASSWORD,
                encoding="utf-8",
                decode_responses=True
            )
            logger.info("Redis connection initialized")

    async def close_redis(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis connection closed")

    def _cart_key(self, user_id: int) -> str:
        """Generate Redis key for user's cart"""
        return f"cart:{user_id}"

    async def add_item(
        self,
        user_id: int,
        product_id: int,
        quantity: int = 1,
        options: Dict = None
    ) -> bool:
        """
        Add item to cart

        Args:
            user_id: Telegram user ID
            product_id: OpenCart product ID
            quantity: Quantity to add
            options: Product options (if any)

        Returns:
            True if successful
        """
        try:
            key = self._cart_key(user_id)

            # Get current quantity
            current_data = await self.redis_client.hget(key, str(product_id))

            if current_data:
                # Update existing item
                item_data = json.loads(current_data)
                item_data["quantity"] += quantity
            else:
                # New item
                item_data = {
                    "product_id": product_id,
                    "quantity": quantity,
                    "options": options or {}
                }

            # Save to Redis
            await self.redis_client.hset(key, str(product_id), json.dumps(item_data))
            await self.redis_client.expire(key, self.expire_seconds)

            logger.info(f"Added product {product_id} (qty: {quantity}) to cart for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to add item to cart: {e}")
            return False

    async def remove_item(self, user_id: int, product_id: int) -> bool:
        """Remove item from cart"""
        try:
            key = self._cart_key(user_id)
            result = await self.redis_client.hdel(key, str(product_id))

            logger.info(f"Removed product {product_id} from cart for user {user_id}")
            return result > 0

        except Exception as e:
            logger.error(f"Failed to remove item from cart: {e}")
            return False

    async def update_quantity(
        self,
        user_id: int,
        product_id: int,
        quantity: int
    ) -> bool:
        """Update item quantity in cart"""
        try:
            if quantity <= 0:
                return await self.remove_item(user_id, product_id)

            key = self._cart_key(user_id)
            current_data = await self.redis_client.hget(key, str(product_id))

            if not current_data:
                return False

            item_data = json.loads(current_data)
            item_data["quantity"] = quantity

            await self.redis_client.hset(key, str(product_id), json.dumps(item_data))
            await self.redis_client.expire(key, self.expire_seconds)

            logger.info(f"Updated product {product_id} quantity to {quantity} for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to update item quantity: {e}")
            return False

    async def get_cart(self, user_id: int) -> Dict[str, Any]:
        """
        Get user's cart with full product details

        Returns:
            Dict with "items" (list) and "total" (float)
        """
        try:
            key = self._cart_key(user_id)
            cart_data = await self.redis_client.hgetall(key)

            if not cart_data:
                return {"items": [], "total": 0.0}

            # Extract product IDs
            product_ids = [int(pid) for pid in cart_data.keys()]

            # Get product details from OpenCart
            products = await opencart_service.get_products_batch(product_ids)

            # Build cart items with full details
            items = []
            total = 0.0

            for product_id_str, item_json in cart_data.items():
                product_id = int(product_id_str)
                item_data = json.loads(item_json)
                quantity = item_data["quantity"]

                if product_id in products:
                    product = products[product_id]
                    price = product["price"]
                    subtotal = price * quantity

                    items.append({
                        "product_id": product_id,
                        "product": product,
                        "quantity": quantity,
                        "options": item_data.get("options", {}),
                        "subtotal": subtotal
                    })

                    total += subtotal

            return {
                "items": items,
                "total": total
            }

        except Exception as e:
            logger.error(f"Failed to get cart: {e}")
            return {"items": [], "total": 0.0}

    async def get_item_count(self, user_id: int) -> int:
        """Get total number of different items in cart"""
        try:
            key = self._cart_key(user_id)
            count = await self.redis_client.hlen(key)
            return count

        except Exception as e:
            logger.error(f"Failed to get cart item count: {e}")
            return 0

    async def clear_cart(self, user_id: int) -> bool:
        """Clear all items from cart"""
        try:
            key = self._cart_key(user_id)
            await self.redis_client.delete(key)

            logger.info(f"Cleared cart for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to clear cart: {e}")
            return False

    async def get_cart_summary(self, user_id: int) -> str:
        """Get formatted cart summary for display"""
        cart = await self.get_cart(user_id)

        if not cart["items"]:
            return "🛒 Ваша корзина пуста"

        from app.utils.formatting import format_cart_summary
        return format_cart_summary(cart)


# Singleton instance
cart_service = CartService()
