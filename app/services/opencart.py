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
        self.base_url = settings.OPENCART_URL
        self.api_username = settings.OPENCART_API_USERNAME
        self.api_key = settings.OPENCART_API_KEY
        self.language_id = 1  # Default language (Russian usually)
        self.store_id = 0  # Default store
        self._api_token = None  # Session token from API login
        self._session = None  # Persistent aiohttp session

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

    async def _get_session(self):
        """Get or create aiohttp session"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close_session(self):
        """Close aiohttp session"""
        if self._session and not self._session.closed:
            await self._session.close()

    async def _authenticate(self) -> bool:
        """
        Authenticate with OpenCart API and get session token
        OpenCart 3.0.2.0 API requires username and key
        """
        try:
            session = await self._get_session()

            # Login endpoint for OpenCart 3.x
            login_url = f"{self.base_url}/index.php?route=api/login"

            # Prepare login data
            data = aiohttp.FormData()
            data.add_field('username', self.api_username)
            data.add_field('key', self.api_key)

            async with session.post(login_url, data=data) as response:
                result = await response.json()

                if 'api_token' in result:
                    self._api_token = result['api_token']
                    logger.info("Successfully authenticated with OpenCart API")
                    return True
                else:
                    logger.error(f"OpenCart API authentication failed: {result}")
                    return False

        except Exception as e:
            logger.error(f"Failed to authenticate with OpenCart API: {e}")
            return False

    async def _ensure_authenticated(self):
        """Ensure we have valid API token"""
        if not self._api_token:
            await self._authenticate()

    async def _api_request(self, route: str, data: Dict = None, method: str = "POST") -> Dict:
        """
        Make API request to OpenCart 3.0.2.0

        Args:
            route: API route (e.g., 'api/cart/add', 'api/customer')
            data: Request data
            method: HTTP method

        Returns:
            API response as dict
        """
        await self._ensure_authenticated()

        if not self._api_token:
            raise Exception("Failed to authenticate with OpenCart API")

        try:
            session = await self._get_session()

            # Build URL with api_token
            url = f"{self.base_url}/index.php?route={route}&api_token={self._api_token}"

            logger.debug(f"OpenCart API request: {method} {url}")

            if method.upper() == "GET":
                async with session.get(url) as response:
                    text = await response.text()
                    try:
                        return await response.json()
                    except:
                        logger.error(f"Failed to parse JSON response: {text}")
                        return {"error": "Invalid JSON response", "response": text}
            else:
                # POST request
                form_data = aiohttp.FormData()
                if data:
                    for key, value in data.items():
                        if isinstance(value, (list, dict)):
                            # For complex data, need to handle properly
                            import json
                            form_data.add_field(key, json.dumps(value))
                        else:
                            form_data.add_field(key, str(value))

                async with session.post(url, data=form_data) as response:
                    text = await response.text()
                    try:
                        return await response.json()
                    except:
                        logger.error(f"Failed to parse JSON response: {text}")
                        return {"error": "Invalid JSON response", "response": text}

        except Exception as e:
            logger.error(f"OpenCart API request failed: {e}")
            raise

    async def create_customer(self, customer_data: Dict) -> Dict:
        """
        Create customer in OpenCart via API
        Note: OpenCart 3.0.2.0 API has limited customer creation support
        This method uses api/customer route if available

        Args:
            customer_data: Dict with firstname, lastname, email, telephone

        Returns:
            Dict with customer_id if successful
        """
        try:
            # Set customer data via API
            data = {
                "firstname": customer_data.get("firstname", ""),
                "lastname": customer_data.get("lastname", "Customer"),
                "email": customer_data.get("email", f"telegram_{customer_data.get('telephone', 'user')}@temp.com"),
                "telephone": customer_data.get("telephone", ""),
            }

            # OpenCart 3.x uses api/customer route
            response = await self._api_request("api/customer", data)

            logger.info(f"Set OpenCart customer data: {response}")

            # Return a pseudo customer ID (will use guest checkout)
            return {"customer_id": 0, "success": True}

        except Exception as e:
            logger.error(f"Failed to set OpenCart customer: {e}")
            # Guest checkout fallback
            return {"customer_id": 0, "success": False, "error": str(e)}

    async def create_order(self, order_data: Dict) -> Dict:
        """
        Create order in OpenCart 3.0.2.0 via API
        Uses multi-step API process: customer -> cart -> payment -> shipping -> order

        Args:
            order_data: Order details including products, customer info, etc.
                Required keys: firstname, lastname, email, telephone, products
                Optional: payment_address, shipping_address, comment

        Returns:
            Dict with order_id if successful
        """
        try:
            # Step 1: Set customer information
            customer_data = {
                "firstname": order_data.get("firstname", ""),
                "lastname": order_data.get("lastname", "Telegram"),
                "email": order_data.get("email", ""),
                "telephone": order_data.get("telephone", ""),
            }
            await self._api_request("api/customer", customer_data)
            logger.debug("Customer data set")

            # Step 2: Clear cart and add products
            await self._api_request("api/cart/products")  # Clear existing cart

            for product in order_data.get("products", []):
                cart_data = {
                    "product_id": product["product_id"],
                    "quantity": product.get("quantity", 1)
                }
                await self._api_request("api/cart/add", cart_data)
                logger.debug(f"Added product {product['product_id']} to cart")

            # Step 3: Set payment address
            payment_addr = order_data.get("payment_address", {})
            payment_address_data = {
                "firstname": payment_addr.get("payment_firstname", order_data.get("firstname", "")),
                "lastname": payment_addr.get("payment_lastname", order_data.get("lastname", "Telegram")),
                "address_1": payment_addr.get("payment_address_1", order_data.get("address", "Самовывоз")),
                "city": payment_addr.get("payment_city", "Moscow"),
                "country_id": payment_addr.get("payment_country_id", "176"),  # Russia
                "zone_id": payment_addr.get("payment_zone_id", "2761"),  # Moscow region
            }
            await self._api_request("api/payment/address", payment_address_data)
            logger.debug("Payment address set")

            # Step 4: Set shipping address (same as payment for simplicity)
            shipping_addr = order_data.get("shipping_address", payment_addr)
            shipping_address_data = {
                "firstname": shipping_addr.get("shipping_firstname", order_data.get("firstname", "")),
                "lastname": shipping_addr.get("shipping_lastname", order_data.get("lastname", "Telegram")),
                "address_1": shipping_addr.get("shipping_address_1", order_data.get("address", "Самовывоз")),
                "city": shipping_addr.get("shipping_city", "Moscow"),
                "country_id": shipping_addr.get("shipping_country_id", "176"),
                "zone_id": shipping_addr.get("shipping_zone_id", "2761"),
            }
            await self._api_request("api/shipping/address", shipping_address_data)
            logger.debug("Shipping address set")

            # Step 5: Set shipping method (typically required)
            # Note: This may fail if no shipping methods are configured
            try:
                shipping_methods = await self._api_request("api/shipping/methods", method="GET")
                # Try to set a default shipping method if available
                logger.debug(f"Available shipping methods: {shipping_methods}")
            except Exception as e:
                logger.warning(f"Could not get shipping methods: {e}")

            # Step 6: Set payment method
            # Note: This may fail if no payment methods are configured
            try:
                payment_methods = await self._api_request("api/payment/methods", method="GET")
                logger.debug(f"Available payment methods: {payment_methods}")
            except Exception as e:
                logger.warning(f"Could not get payment methods: {e}")

            # Step 7: Add comment if provided
            if order_data.get("comment"):
                comment_data = {"comment": order_data["comment"]}
                await self._api_request("api/order/comment", comment_data)

            # Step 8: Confirm and create the order
            confirm_response = await self._api_request("api/order/add")

            logger.info(f"OpenCart order created: {confirm_response}")

            # Extract order_id from response
            if "order_id" in confirm_response:
                return {
                    "order_id": confirm_response["order_id"],
                    "success": True
                }
            else:
                # Return success but without order_id
                logger.warning("Order created but no order_id in response")
                return {"success": True, "response": confirm_response}

        except Exception as e:
            logger.error(f"Failed to create OpenCart order: {e}")
            return {"success": False, "error": str(e)}

    async def update_order_status(self, order_id: int, status_id: int):
        """
        Update order status in OpenCart
        Note: This typically requires admin API access in OpenCart 3.x
        May not work with standard API user
        """
        try:
            data = {
                "order_id": order_id,
                "order_status_id": status_id
            }

            response = await self._api_request("api/order/edit", data)
            logger.info(f"Updated OpenCart order {order_id} to status {status_id}")
            return response

        except Exception as e:
            logger.error(f"Failed to update OpenCart order status: {e}")
            # Status update might not be available via API
            logger.warning("Order status update may require admin access or database update")
            return {"success": False, "error": str(e)}


# Singleton instance
opencart_service = OpenCartService()
