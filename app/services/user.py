"""
User management service
"""
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import User
from app.utils.logger import get_logger

logger = get_logger(__name__)


class UserService:
    """Service for managing bot users"""

    async def get_or_create_user(
        self,
        db: AsyncSession,
        user_id: int,
        username: str = None,
        first_name: str = None,
        last_name: str = None
    ) -> User:
        """
        Get existing user or create new one

        Args:
            db: Database session
            user_id: Telegram user ID
            username: Telegram username
            first_name: User's first name
            last_name: User's last name

        Returns:
            User object
        """
        try:
            # Try to get existing user
            query = select(User).where(User.id == user_id)
            result = await db.execute(query)
            user = result.scalar_one_or_none()

            if user:
                # Update user info if changed
                if (username and user.username != username) or \
                   (first_name and user.first_name != first_name) or \
                   (last_name and user.last_name != last_name):
                    user.username = username
                    user.first_name = first_name
                    user.last_name = last_name
                    user.updated_at = datetime.utcnow()
                    await db.commit()
                    await db.refresh(user)

                return user

            # Create new user
            user = User(
                id=user_id,
                username=username,
                first_name=first_name,
                last_name=last_name
            )

            db.add(user)
            await db.commit()
            await db.refresh(user)

            logger.info(f"Created new user: {user_id} ({first_name})")
            return user

        except Exception as e:
            logger.error(f"Failed to get or create user: {e}")
            await db.rollback()
            raise

    async def get_user(self, db: AsyncSession, user_id: int) -> Optional[User]:
        """Get user by ID"""
        try:
            query = select(User).where(User.id == user_id)
            result = await db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get user: {e}")
            return None

    async def update_phone(
        self,
        db: AsyncSession,
        user_id: int,
        phone: str
    ) -> bool:
        """Update user's phone number"""
        try:
            query = (
                update(User)
                .where(User.id == user_id)
                .values(phone=phone, updated_at=datetime.utcnow())
            )
            await db.execute(query)
            await db.commit()

            logger.info(f"Updated phone for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to update phone: {e}")
            await db.rollback()
            return False

    async def update_email(
        self,
        db: AsyncSession,
        user_id: int,
        email: str
    ) -> bool:
        """Update user's email"""
        try:
            query = (
                update(User)
                .where(User.id == user_id)
                .values(email=email, updated_at=datetime.utcnow())
            )
            await db.execute(query)
            await db.commit()

            logger.info(f"Updated email for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to update email: {e}")
            await db.rollback()
            return False

    async def update_opencart_id(
        self,
        db: AsyncSession,
        user_id: int,
        opencart_customer_id: int
    ) -> bool:
        """Link user to OpenCart customer"""
        try:
            query = (
                update(User)
                .where(User.id == user_id)
                .values(opencart_customer_id=opencart_customer_id, updated_at=datetime.utcnow())
            )
            await db.execute(query)
            await db.commit()

            logger.info(f"Linked user {user_id} to OpenCart customer {opencart_customer_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to update OpenCart ID: {e}")
            await db.rollback()
            return False

    async def get_all_users(self, db: AsyncSession, limit: int = 100) -> list[User]:
        """Get all users (for admin)"""
        try:
            query = select(User).order_by(User.created_at.desc()).limit(limit)
            result = await db.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get all users: {e}")
            return []


# Singleton instance
user_service = UserService()
