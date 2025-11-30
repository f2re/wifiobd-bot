"""
Checkout handlers for VK bot (simplified version)
"""
from vkbottle.bot import Bot, Message
from vkbottle import Keyboard, Callback, OpenLink, KeyboardButtonColor

from app.services.cart import cart_service
from app.keyboards.inline import VKKeyboards
from app.utils.logger import get_logger
from app.utils.formatting import format_price

logger = get_logger(__name__)


def register_handlers(bot: Bot):
    """Register checkout handlers"""

    @bot.on.message(payload={'action': 'checkout'})
    async def start_checkout(message: Message):
        """Start checkout process"""
        try:
            user_id = message.from_id

            # Get cart
            cart = await cart_service.get_cart(user_id)

            if not cart["items"]:
                await message.answer("🛒 Корзина пуста", keyboard=VKKeyboards.main_menu())
                return

            # Build order summary
            items_text = []
            for item in cart["items"]:
                product = item["product"]
                if isinstance(product, dict):
                    name = product.get("name", "Товар")
                    price = product.get("price", 0)
                else:
                    name = product.name
                    price = product.price

                items_text.append(
                    f"• {name}\n  {format_price(price)} × {item['quantity']} = {format_price(item['subtotal'])}"
                )

            text = f"""
📝 <b>Оформление заказа</b>

<b>Товары:</b>
{chr(10).join(items_text)}

━━━━━━━━━━━━━━━━━
💰 <b>Итого: {format_price(cart['total'])}</b>

Для оформления заказа:
1. Напишите ваш номер телефона в формате: +7XXXXXXXXXX
2. После этого вы получите ссылку на оплату через YooKassa

Или нажмите кнопку "Перейти к оплате" ниже.
"""

            # Create keyboard with payment button
            keyboard = VKKeyboards.payment_method()

            await message.answer(text, keyboard=keyboard)

        except Exception as e:
            logger.error(f"Error in checkout: {e}", exc_info=True)
            await message.answer("❌ Произошла ошибка")

    @bot.on.message(payload={'action': 'cancel_checkout'})
    async def cancel_checkout(message: Message):
        """Cancel checkout"""
        await message.answer(
            "❌ Оформление заказа отменено",
            keyboard=VKKeyboards.main_menu()
        )

    logger.info("Checkout handlers registered")
