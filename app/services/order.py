"""
Order management service
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models import Order, User
from app.utils.logger import get_logger

logger = get_logger(__name__)


class OrderService:
    """Service for managing orders"""

    async def create_order(
        self,
        db: AsyncSession,
        user_id: int,
        cart: Dict[str, Any],
        delivery_data: Dict[str, Any]
    ) -> Order:
        """
        Create new order from cart

        Args:
            db: Database session
            user_id: User's Telegram ID
            cart: Cart data with items and total
            delivery_data: Delivery information (phone, address, comment, etc.)

        Returns:
            Created Order object
        """
        try:
            # Prepare order items
            items = []
            for cart_item in cart["items"]:
                product = cart_item["product"]
                items.append({
                    "product_id": product["product_id"],
                    "name": product["name"],
                    "model": product["model"],
                    "price": product["price"],
                    "quantity": cart_item["quantity"]
                })

            # Create order
            order = Order(
                user_id=user_id,
                amount=cart["total"],
                status="pending",
                customer_name=delivery_data.get("name", ""),
                customer_phone=delivery_data.get("phone", ""),
                customer_email=delivery_data.get("email"),
                delivery_address=delivery_data.get("address"),
                delivery_comment=delivery_data.get("comment"),
                items=items
            )

            db.add(order)
            await db.commit()
            await db.refresh(order)

            logger.info(f"Created order {order.id} for user {user_id}, amount: {order.amount}")
            return order

        except Exception as e:
            logger.error(f"Failed to create order: {e}")
            await db.rollback()
            raise

    async def get_order(
        self,
        db: AsyncSession,
        order_id: int
    ) -> Optional[Order]:
        """Get order by ID"""
        try:
            query = select(Order).where(Order.id == order_id)
            result = await db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get order: {e}")
            return None

    async def get_order_with_user(
        self,
        db: AsyncSession,
        order_id: int
    ) -> Optional[Order]:
        """Get order with user details"""
        try:
            query = (
                select(Order)
                .options(selectinload(Order.user))
                .where(Order.id == order_id)
            )
            result = await db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get order with user: {e}")
            return None

    async def update_status(
        self,
        db: AsyncSession,
        order_id: int,
        status: str
    ) -> bool:
        """Update order status"""
        try:
            updates = {
                "status": status,
                "updated_at": datetime.utcnow()
            }

            # Set paid_at timestamp when order is paid
            if status == "paid":
                updates["paid_at"] = datetime.utcnow()

            query = update(Order).where(Order.id == order_id).values(**updates)
            await db.execute(query)
            await db.commit()

            logger.info(f"Updated order {order_id} status to {status}")
            return True

        except Exception as e:
            logger.error(f"Failed to update order status: {e}")
            await db.rollback()
            return False

    async def update_payment_label(
        self,
        db: AsyncSession,
        order_id: int,
        label: str
    ) -> bool:
        """Update YooMoney payment label for order"""
        try:
            query = (
                update(Order)
                .where(Order.id == order_id)
                .values(yoomoney_label=label, updated_at=datetime.utcnow())
            )
            await db.execute(query)
            await db.commit()

            logger.info(f"Updated payment label for order {order_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to update payment label: {e}")
            await db.rollback()
            return False

    async def update_opencart_order_id(
        self,
        db: AsyncSession,
        order_id: int,
        opencart_order_id: int
    ) -> bool:
        """Link order to OpenCart order"""
        try:
            query = (
                update(Order)
                .where(Order.id == order_id)
                .values(opencart_order_id=opencart_order_id, updated_at=datetime.utcnow())
            )
            await db.execute(query)
            await db.commit()

            logger.info(f"Linked order {order_id} to OpenCart order {opencart_order_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to update OpenCart order ID: {e}")
            await db.rollback()
            return False

    async def get_user_orders(
        self,
        db: AsyncSession,
        user_id: int,
        limit: int = 10
    ) -> List[Order]:
        """Get user's orders"""
        try:
            query = (
                select(Order)
                .where(Order.user_id == user_id)
                .order_by(Order.created_at.desc())
                .limit(limit)
            )
            result = await db.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get user orders: {e}")
            return []

    async def get_recent_orders(
        self,
        db: AsyncSession,
        limit: int = 20
    ) -> List[Order]:
        """Get recent orders (for admin)"""
        try:
            query = (
                select(Order)
                .options(selectinload(Order.user))
                .order_by(Order.created_at.desc())
                .limit(limit)
            )
            result = await db.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get recent orders: {e}")
            return []

    async def get_pending_orders(self, db: AsyncSession) -> List[Order]:
        """Get all pending orders"""
        try:
            query = (
                select(Order)
                .where(Order.status == "pending")
                .order_by(Order.created_at.desc())
            )
            result = await db.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get pending orders: {e}")
            return []


# Singleton instance
order_service = OrderService()
