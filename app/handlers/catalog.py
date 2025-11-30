"""
Catalog browsing handlers for VK bot (categories and products)
"""
from vkbottle.bot import Bot, Message
from vkbottle import Callback

from app.services.opencart import opencart_service
from app.services.vk_service import vk_photo_service
from app.keyboards.inline import VKKeyboards
from app.utils.logger import get_logger
from app.utils.formatting import format_product_card
from config import settings

logger = get_logger(__name__)


def register_handlers(bot: Bot):
    """Register catalog handlers"""

    @bot.on.message(text=["🛍 Каталог", "🛍 каталог", "Каталог", "каталог"])
    async def show_catalog_text(message: Message):
        """Show catalog from text button"""
        try:
            categories = await opencart_service.get_root_categories()

            if not categories:
                await message.answer(
                    "📂 <b>Каталог пуст</b>\n\nВ данный момент категории не доступны.",
                    keyboard=VKKeyboards.main_menu()
                )
                return

            # Find "Магазин" category
            shop_category = None
            for category in categories:
                if category['name'].lower() == 'магазин':
                    shop_category = category
                    break

            if shop_category:
                # Get subcategories of "Магазин"
                subcategories = await opencart_service.get_subcategories(shop_category['category_id'])

                if subcategories:
                    await message.answer(
                        "📂 <b>Каталог товаров</b>\n\nВыберите категорию:",
                        keyboard=VKKeyboards.catalog_categories(subcategories)
                    )
                else:
                    # Show products from "Магазин"
                    products = await opencart_service.get_products_by_category(
                        shop_category['category_id'],
                        limit=settings.PRODUCTS_PER_PAGE,
                        offset=0
                    )

                    if products:
                        # Format products list
                        text = "📂 <b>Каталог товаров</b>\n\nВыберите товар:\n\n"
                        for product in products:
                            text += f"• {product['name']} - {product['price']}₽\n"

                        # For VK, we'll use callback buttons for products
                        await message.answer(text, keyboard=VKKeyboards.back_button('main_menu'))
                    else:
                        await message.answer(
                            "📂 <b>Каталог</b>\n\n😔 В данный момент товары не доступны.",
                            keyboard=VKKeyboards.main_menu()
                        )
            else:
                # Show all root categories
                await message.answer(
                    "📂 <b>Каталог товаров</b>\n\nВыберите категорию:",
                    keyboard=VKKeyboards.catalog_categories(categories)
                )

        except Exception as e:
            logger.error(f"Error showing catalog: {e}", exc_info=True)
            await message.answer(
                "❌ Произошла ошибка при загрузке каталога",
                keyboard=VKKeyboards.main_menu()
            )

    @bot.on.message(payload={'action': 'catalog'})
    async def show_catalog_callback(message: Message):
        """Show catalog from callback"""
        await show_catalog_text(message)

    @bot.on.message(payload={'action': 'category'})
    async def show_category(message: Message):
        """Show category contents"""
        try:
            payload = message.get_payload_json()
            category_id = payload.get('id')

            if not category_id:
                await message.answer("❌ Ошибка: категория не указана")
                return

            # Get category details
            category = await opencart_service.get_category_details(category_id)

            if not category:
                await message.answer("❌ Категория не найдена")
                return

            # Check for subcategories
            subcategories = await opencart_service.get_subcategories(category_id)

            if subcategories:
                # Show subcategories
                await message.answer(
                    f"📁 <b>{category['name']}</b>\n\nВыберите подкатегорию:",
                    keyboard=VKKeyboards.catalog_categories(subcategories)
                )
            else:
                # Show products
                products = await opencart_service.get_products_by_category(
                    category_id,
                    limit=settings.PRODUCTS_PER_PAGE,
                    offset=0
                )

                if not products:
                    await message.answer(
                        f"📁 <b>{category['name']}</b>\n\n😔 В этой категории пока нет товаров.",
                        keyboard=VKKeyboards.back_button('catalog')
                    )
                else:
                    # Format products list
                    text = f"📁 <b>{category['name']}</b>\n\nТовары:\n\n"
                    for i, product in enumerate(products, 1):
                        text += f"{i}. {product['name']}\n💰 {product['price']}₽\n\n"

                    # Create keyboard with product buttons
                    from vkbottle import Keyboard, KeyboardButtonColor, Callback as VKCallback
                    keyboard = Keyboard(inline=True)

                    for i, product in enumerate(products[:10]):  # Limit to 10 products per page
                        keyboard.add(
                            VKCallback(
                                label=f"{i+1}. {product['name'][:20]}...",
                                payload={'action': 'product', 'id': product['product_id']}
                            )
                        )
                        if (i + 1) % 2 == 0:
                            keyboard.row()

                    keyboard.row()
                    keyboard.add(VKCallback(label="🔙 Назад", payload={'action': 'catalog'}))

                    await message.answer(text, keyboard=keyboard.get_json())

        except Exception as e:
            logger.error(f"Error showing category: {e}", exc_info=True)
            await message.answer("❌ Произошла ошибка при загрузке категории")

    @bot.on.message(payload={'action': 'product'})
    async def show_product(message: Message):
        """Show product details"""
        try:
            payload = message.get_payload_json()
            product_id = payload.get('id')

            if not product_id:
                await message.answer("❌ Ошибка: товар не указан")
                return

            # Get product details
            product = await opencart_service.get_product_details(product_id)

            if not product:
                await message.answer("❌ Товар не найден")
                return

            # Format product card
            product_url = f"{settings.OPENCART_URL}/index.php?route=product/product&product_id={product_id}"
            text = format_product_card(product, product_url=product_url)

            # Get product image
            image_attachment = None
            if product.get('image'):
                image_url = f"{settings.OPENCART_URL}/image/{product['image']}"
                try:
                    # Upload photo to VK
                    image_attachment = await vk_photo_service.upload_photo(image_url)
                except Exception as img_error:
                    logger.warning(f"Failed to upload product image: {img_error}")

            # Check if product is in stock
            in_stock = product.get('in_stock', False)

            # Create keyboard
            keyboard_json = VKKeyboards.product_actions(
                product_id,
                in_cart=False  # TODO: check if product is in cart
            )

            # Send message with or without photo
            if image_attachment:
                await message.answer(
                    message=text,
                    attachment=image_attachment,
                    keyboard=keyboard_json
                )
            else:
                await message.answer(
                    message=text,
                    keyboard=keyboard_json
                )

        except Exception as e:
            logger.error(f"Error showing product: {e}", exc_info=True)
            await message.answer("❌ Произошла ошибка при загрузке товара")

    @bot.on.message(payload={'action': 'back_to_menu'})
    async def back_to_menu(message: Message):
        """Return to main menu"""
        await message.answer(
            "Главное меню:",
            keyboard=VKKeyboards.main_menu()
        )

    @bot.on.message(payload={'action': 'back_to_category'})
    async def back_to_category(message: Message):
        """Go back to category list"""
        await show_catalog_text(message)

    logger.info("Catalog handlers registered")
