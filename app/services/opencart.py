"""
OpenCart integration service
Hybrid approach: Read from DB, Write via API
"""
from typing import List, Dict, Any, Optional
import aiohttp
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.opencart_models import (
    OCCategory, OCCategoryDescription, OCCategoryToStore,
    OCProduct, OCProductDescription, OCProductToCategory,
    OCCustomer, OCOrder, OCOrderProduct
)
from config.opencart_db import OpenCartSessionLocal
from config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class OpenCartService:
    """Service for OpenCart integration"""

    def __init__(self):
        self.api_url = settings.OPENCART_API_URL
        self.api_token = settings.OPENCART_API_TOKEN
        self.base_url = settings.OPENCART_URL
        self.language_id = 1  # Default language (Russian usually)
        self.store_id = 0  # Default store

    async def _get_db_session(self) -> AsyncSession:
        """Get OpenCart database session"""
        return OpenCartSessionLocal()

    # ==================== CATALOG OPERATIONS (READ FROM DB) ====================

    async def get_root_categories(self) -> List[Dict[str, Any]]:
        """Get root level categories (parent_id = 0)"""
        async with OpenCartSessionLocal() as session:
            query = (
                select(OCCategory, OCCategoryDescription)
                .join(OCCategoryDescription, OCCategory.category_id == OCCategoryDescription.category_id)
                .where(
                    and_(
                        OCCategory.parent_id == 0,
                        OCCategory.status == True,
                        OCCategoryDescription.language_id == self.language_id
                    )
                )
                .order_by(OCCategory.sort_order, OCCategoryDescription.name)
            )

            result = await session.execute(query)
            categories = []

            for category, description in result:
                categories.append({
                    "category_id": category.category_id,
                    "name": description.name,
                    "image": category.image,
                    "parent_id": category.parent_id,
                    "sort_order": category.sort_order
                })

            return categories

    async def get_subcategories(self, parent_id: int) -> List[Dict[str, Any]]:
        """Get subcategories of a specific category"""
        async with OpenCartSessionLocal() as session:
            query = (
                select(OCCategory, OCCategoryDescription)
                .join(OCCategoryDescription, OCCategory.category_id == OCCategoryDescription.category_id)
                .where(
                    and_(
                        OCCategory.parent_id == parent_id,
                        OCCategory.status == True,
                        OCCategoryDescription.language_id == self.language_id
                    )
                )
                .order_by(OCCategory.sort_order, OCCategoryDescription.name)
            )

            result = await session.execute(query)
            categories = []

            for category, description in result:
                categories.append({
                    "category_id": category.category_id,
                    "name": description.name,
                    "image": category.image,
                    "parent_id": category.parent_id,
                    "sort_order": category.sort_order
                })

            return categories

    async def get_category_details(self, category_id: int) -> Optional[Dict[str, Any]]:
        """Get category details by ID"""
        async with OpenCartSessionLocal() as session:
            query = (
                select(OCCategory, OCCategoryDescription)
                .join(OCCategoryDescription, OCCategory.category_id == OCCategoryDescription.category_id)
                .where(
                    and_(
                        OCCategory.category_id == category_id,
                        OCCategoryDescription.language_id == self.language_id
                    )
                )
            )

            result = await session.execute(query)
            row = result.first()

            if not row:
                return None

            category, description = row

            return {
                "category_id": category.category_id,
                "name": description.name,
                "description": description.description,
                "image": category.image,
                "parent_id": category.parent_id,
                "sort_order": category.sort_order
            }

    async def get_products_by_category(
        self,
        category_id: int,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get products in a category with pagination"""
        async with OpenCartSessionLocal() as session:
            query = (
                select(OCProduct, OCProductDescription)
                .join(OCProductDescription, OCProduct.product_id == OCProductDescription.product_id)
                .join(OCProductToCategory, OCProduct.product_id == OCProductToCategory.product_id)
                .where(
                    and_(
                        OCProductToCategory.category_id == category_id,
                        OCProduct.status == True,
                        OCProductDescription.language_id == self.language_id
                    )
                )
                .order_by(OCProduct.sort_order, OCProductDescription.name)
                .limit(limit)
                .offset(offset)
            )

            result = await session.execute(query)
            products = []

            for product, description in result:
                products.append({
                    "product_id": product.product_id,
                    "name": description.name,
                    "description": description.description,
                    "model": product.model,
                    "price": float(product.price),
                    "quantity": product.quantity,
                    "image": product.image,
                    "category_id": category_id
                })

            return products

    async def get_product_details(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed product information"""
        async with OpenCartSessionLocal() as session:
            query = (
                select(OCProduct, OCProductDescription)
                .join(OCProductDescription, OCProduct.product_id == OCProductDescription.product_id)
                .where(
                    and_(
                        OCProduct.product_id == product_id,
                        OCProductDescription.language_id == self.language_id
                    )
                )
            )

            result = await session.execute(query)
            row = result.first()

            if not row:
                return None

            product, description = row

            # Get category for this product
            cat_query = select(OCProductToCategory).where(
                OCProductToCategory.product_id == product_id
            ).limit(1)
            cat_result = await session.execute(cat_query)
            cat_row = cat_result.first()
            category_id = cat_row[0].category_id if cat_row else None

            return {
                "product_id": product.product_id,
                "name": description.name,
                "description": description.description,
                "model": product.model,
                "sku": product.sku,
                "price": float(product.price),
                "quantity": product.quantity,
                "image": product.image,
                "category_id": category_id,
                "in_stock": product.quantity > 0
            }

    async def get_products_batch(self, product_ids: List[int]) -> Dict[int, Dict[str, Any]]:
        """Get multiple products by IDs in one query"""
        async with OpenCartSessionLocal() as session:
            query = (
                select(OCProduct, OCProductDescription)
                .join(OCProductDescription, OCProduct.product_id == OCProductDescription.product_id)
                .where(
                    and_(
                        OCProduct.product_id.in_(product_ids),
                        OCProductDescription.language_id == self.language_id
                    )
                )
            )

            result = await session.execute(query)
            products = {}

            for product, description in result:
                products[product.product_id] = {
                    "product_id": product.product_id,
                    "name": description.name,
                    "description": description.description,
                    "model": product.model,
                    "price": float(product.price),
                    "quantity": product.quantity,
                    "image": product.image
                }

            return products

    async def search_products(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search products by name"""
        async with OpenCartSessionLocal() as session:
            search_query = (
                select(OCProduct, OCProductDescription)
                .join(OCProductDescription, OCProduct.product_id == OCProductDescription.product_id)
                .where(
                    and_(
                        OCProduct.status == True,
                        OCProductDescription.language_id == self.language_id,
                        or_(
                            OCProductDescription.name.ilike(f"%{query}%"),
                            OCProduct.model.ilike(f"%{query}%")
                        )
                    )
                )
                .limit(limit)
            )

            result = await session.execute(search_query)
            products = []

            for product, description in result:
                products.append({
                    "product_id": product.product_id,
                    "name": description.name,
                    "model": product.model,
                    "price": float(product.price),
                    "quantity": product.quantity,
                    "image": product.image
                })

            return products

    # ==================== API OPERATIONS (WRITE VIA API) ====================

    async def _api_request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """Make API request to OpenCart"""
        url = f"{self.api_url}/{endpoint}"

        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        # Add API token if available
        params = {}
        if self.api_token:
            params["token"] = self.api_token

        try:
            async with aiohttp.ClientSession() as session:
                if method.upper() == "GET":
                    async with session.get(url, params=params, headers=headers) as response:
                        return await response.json()
                elif method.upper() == "POST":
                    async with session.post(url, params=params, data=data, headers=headers) as response:
                        return await response.json()
                elif method.upper() == "PUT":
                    async with session.put(url, params=params, data=data, headers=headers) as response:
                        return await response.json()
                elif method.upper() == "DELETE":
                    async with session.delete(url, params=params, headers=headers) as response:
                        return await response.json()
        except Exception as e:
            logger.error(f"OpenCart API request failed: {e}")
            raise

    async def create_customer(self, customer_data: Dict) -> Dict:
        """
        Create customer in OpenCart via API

        Args:
            customer_data: Dict with firstname, lastname, email, telephone
        """
        try:
            data = {
                "firstname": customer_data.get("firstname", ""),
                "lastname": customer_data.get("lastname", "Customer"),
                "email": customer_data.get("email", ""),
                "telephone": customer_data.get("telephone", ""),
                "password": customer_data.get("password", "telegram_user"),
                "confirm": customer_data.get("password", "telegram_user"),
                "newsletter": 0,
                "customer_group_id": 1
            }

            response = await self._api_request("POST", "customer/add", data)
            logger.info(f"Created OpenCart customer: {response}")
            return response

        except Exception as e:
            logger.error(f"Failed to create OpenCart customer: {e}")
            # Fallback: create directly in DB (not recommended in production)
            raise

    async def create_order(self, order_data: Dict) -> Dict:
        """
        Create order in OpenCart via API

        Args:
            order_data: Order details including products, customer info, etc.
        """
        try:
            # Prepare order data for OpenCart API
            data = {
                "customer_id": order_data.get("customer_id", 0),
                "customer_group_id": order_data.get("customer_group_id", 1),
                "firstname": order_data.get("firstname", ""),
                "lastname": order_data.get("lastname", ""),
                "email": order_data.get("email", ""),
                "telephone": order_data.get("telephone", ""),
                "payment_method": order_data.get("payment_method", "YooMoney"),
                "payment_code": "yoomoney",
                "shipping_method": order_data.get("shipping_method", "Самовывоз"),
                "shipping_code": "pickup.pickup",
                "products": order_data.get("products", []),
                "totals": order_data.get("totals", []),
                "comment": order_data.get("comment", ""),
                "order_status_id": order_data.get("order_status_id", 1)
            }

            # Add addresses
            if "payment_address" in order_data:
                data.update(order_data["payment_address"])
            if "shipping_address" in order_data:
                data.update(order_data["shipping_address"])

            response = await self._api_request("POST", "order/add", data)
            logger.info(f"Created OpenCart order: {response}")
            return response

        except Exception as e:
            logger.error(f"Failed to create OpenCart order: {e}")
            raise

    async def update_order_status(self, order_id: int, status_id: int):
        """Update order status in OpenCart"""
        try:
            data = {
                "order_id": order_id,
                "order_status_id": status_id
            }

            response = await self._api_request("POST", "order/update", data)
            logger.info(f"Updated OpenCart order {order_id} to status {status_id}")
            return response

        except Exception as e:
            logger.error(f"Failed to update OpenCart order status: {e}")
            raise


# Singleton instance
opencart_service = OpenCartService()
