"""
Shopping cart handlers for VK bot
"""
from vkbottle.bot import Bot, Message

from app.services.cart import cart_service
from app.services.opencart import opencart_service
from app.keyboards.inline import VKKeyboards
from app.utils.logger import get_logger
from app.utils.formatting import format_cart_summary

logger = get_logger(__name__)


def register_handlers(bot: Bot):
    """Register cart handlers"""

    @bot.on.message(payload={'action': 'add_to_cart'})
    async def add_to_cart(message: Message):
        """Add product to cart"""
        try:
            payload = message.get_payload_json()
            product_id = payload.get('product_id')

            if not product_id:
                await message.answer("❌ Ошибка: товар не указан")
                return

            user_id = message.from_id

            # Get product details
            product = await opencart_service.get_product_details(product_id)

            if not product:
                await message.answer("❌ Товар не найден")
                return

            if not product.get('in_stock', False):
                await message.answer("❌ Товар отсутствует на складе")
                return

            # Add to cart
            success = await cart_service.add_item(user_id, product_id, quantity=1)

            if success:
                count = await cart_service.get_item_count(user_id)
                await message.answer(
                    f"✅ Товар добавлен в корзину!\n🛒 Товаров в корзине: {count}",
                    keyboard=VKKeyboards.main_menu()
                )
            else:
                await message.answer("❌ Не удалось добавить товар в корзину")

        except Exception as e:
            logger.error(f"Error adding to cart: {e}", exc_info=True)
            await message.answer("❌ Произошла ошибка")

    @bot.on.message(text=["🛒 Корзина", "🛒 корзина", "Корзина", "корзина"])
    async def show_cart_text(message: Message):
        """Show shopping cart from text button"""
        await show_cart_handler(message)

    @bot.on.message(payload={'action': 'cart'})
    async def show_cart_callback(message: Message):
        """Show shopping cart from callback"""
        await show_cart_handler(message)

    async def show_cart_handler(message: Message):
        """Show shopping cart"""
        try:
            user_id = message.from_id

            # Get cart
            cart = await cart_service.get_cart(user_id)

            if not cart["items"]:
                await message.answer(
                    "🛒 <b>Ваша корзина пуста</b>\n\nДобавьте товары из каталога.",
                    keyboard=VKKeyboards.main_menu()
                )
            else:
                text = format_cart_summary(cart)
                keyboard = VKKeyboards.cart_actions(has_items=True)
                await message.answer(text, keyboard=keyboard)

        except Exception as e:
            logger.error(f"Error showing cart: {e}", exc_info=True)
            await message.answer("❌ Произошла ошибка при загрузке корзины")

    @bot.on.message(payload={'action': 'remove_from_cart'})
    async def remove_from_cart(message: Message):
        """Remove item from cart"""
        try:
            payload = message.get_payload_json()
            product_id = payload.get('product_id')

            if not product_id:
                await message.answer("❌ Ошибка: товар не указан")
                return

            user_id = message.from_id

            # Remove from cart
            success = await cart_service.remove_item(user_id, product_id)

            if success:
                await message.answer("🗑 Товар удален из корзины")

                # Show updated cart
                cart = await cart_service.get_cart(user_id)

                if not cart["items"]:
                    await message.answer(
                        "🛒 <b>Ваша корзина пуста</b>\n\nДобавьте товары из каталога.",
                        keyboard=VKKeyboards.main_menu()
                    )
                else:
                    text = format_cart_summary(cart)
                    await message.answer(text, keyboard=VKKeyboards.cart_actions(has_items=True))
            else:
                await message.answer("❌ Товар не найден в корзине")

        except Exception as e:
            logger.error(f"Error removing from cart: {e}", exc_info=True)
            await message.answer("❌ Произошла ошибка")

    @bot.on.message(payload={'action': 'clear_cart'})
    async def clear_cart(message: Message):
        """Clear entire cart"""
        try:
            user_id = message.from_id

            # Clear cart
            await cart_service.clear_cart(user_id)

            await message.answer(
                "🛒 <b>Корзина очищена</b>\n\nВсе товары удалены из корзины.",
                keyboard=VKKeyboards.main_menu()
            )

        except Exception as e:
            logger.error(f"Error clearing cart: {e}", exc_info=True)
            await message.answer("❌ Произошла ошибка")

    @bot.on.message(payload={'action': 'back_to_cart'})
    async def back_to_cart(message: Message):
        """Return to cart"""
        await show_cart_handler(message)

    @bot.on.message(text=["📦 Мои заказы", "📦 мои заказы", "Заказы", "заказы"])
    async def show_my_orders(message: Message):
        """Show user's orders"""
        try:
            from app.database import get_db
            from app.services.order import order_service
            from app.utils.formatting import format_price, format_date

            user_id = message.from_id

            # Get user's orders
            async with get_db() as db:
                orders = await order_service.get_user_orders(db, user_id, limit=10)

            if not orders:
                await message.answer(
                    "📦 <b>История заказов</b>\n\nУ вас пока нет заказов.",
                    keyboard=VKKeyboards.main_menu()
                )
                return

            # Build orders list
            text = "📦 <b>Ваши заказы:</b>\n\n"

            for order in orders:
                status_emoji = {
                    "pending": "⏳",
                    "paid": "✅",
                    "cancelled": "❌",
                    "completed": "🎉"
                }.get(order.status, "❓")
                status_text = {
                    "pending": "Ожидает оплаты",
                    "paid": "Оплачен",
                    "cancelled": "Отменен",
                    "completed": "Выполнен"
                }.get(order.status, "Неизвестно")

                text += f"""
{status_emoji} <b>Заказ #{order.id}</b>
💰 Сумма: {format_price(order.amount)}
📅 Дата: {format_date(order.created_at)}
📊 Статус: {status_text}
━━━━━━━━━━━━
"""

            await message.answer(text, keyboard=VKKeyboards.main_menu())

        except Exception as e:
            logger.error(f"Error showing orders: {e}", exc_info=True)
            await message.answer("❌ Произошла ошибка")

    logger.info("Cart handlers registered")
