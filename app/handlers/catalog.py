"""
Catalog browsing handlers (categories and products)
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, InputMediaPhoto
from aiogram.exceptions import TelegramBadRequest

from app.services.opencart import opencart_service
from app.keyboards.inline import (
    categories_keyboard,
    products_keyboard,
    product_card_keyboard,
    back_to_main_menu_keyboard
)
from app.utils.logger import get_logger
from app.utils.formatting import format_product_card
from config import settings

logger = get_logger(__name__)

router = Router()


@router.callback_query(F.data == "catalog")
async def show_catalog(callback: CallbackQuery):
    """Show catalog - auto-redirect to 'Магазин' category"""
    try:
        categories = await opencart_service.get_root_categories()

        if not categories:
            # Check if current message has photo
            has_photo = callback.message.photo is not None and len(callback.message.photo) > 0

            text = "📂 <b>Каталог пуст</b>\n\nВ данный момент категории не доступны."
            keyboard = back_to_main_menu_keyboard()

            if has_photo:
                await callback.message.delete()
                await callback.message.answer(
                    text,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
            else:
                try:
                    await callback.message.edit_text(
                        text,
                        reply_markup=keyboard,
                        parse_mode="HTML"
                    )
                except TelegramBadRequest as e:
                    if "message is not modified" in str(e):
                        pass
                    else:
                        raise
            await callback.answer()
            return

        # Find "Магазин" category by name
        shop_category = None
        for category in categories:
            if category['name'].lower() == 'магазин':
                shop_category = category
                break

        # If "Магазин" category found, redirect to it directly
        if shop_category:
            # Get subcategories of "Магазин"
            shop_category_id = shop_category['category_id']
            subcategories = await opencart_service.get_subcategories(shop_category_id)

            # Check if current message has photo
            has_photo = callback.message.photo is not None and len(callback.message.photo) > 0

            if subcategories:
                # Show subcategories of "Магазин"
                text = "📂 <b>Каталог товаров</b>\n\nВыберите категорию:"
                keyboard = categories_keyboard(subcategories, 0)  # parent_id=0 to go back to main menu

                if has_photo:
                    await callback.message.delete()
                    await callback.message.answer(
                        text,
                        reply_markup=keyboard,
                        parse_mode="HTML"
                    )
                else:
                    try:
                        await callback.message.edit_text(
                            text,
                            reply_markup=keyboard,
                            parse_mode="HTML"
                        )
                    except TelegramBadRequest as e:
                        if "message is not modified" in str(e):
                            pass
                        else:
                            raise
            else:
                # No subcategories, show products from "Магазин"
                products = await opencart_service.get_products_by_category(
                    shop_category_id,
                    limit=settings.PRODUCTS_PER_PAGE,
                    offset=0
                )

                if products:
                    text = "📂 <b>Каталог товаров</b>\n\nВыберите товар:"
                    has_next = len(products) == settings.PRODUCTS_PER_PAGE
                    keyboard = products_keyboard(products, shop_category_id, 0, has_next, 0)

                    if has_photo:
                        await callback.message.delete()
                        await callback.message.answer(
                            text,
                            reply_markup=keyboard,
                            parse_mode="HTML"
                        )
                    else:
                        try:
                            await callback.message.edit_text(
                                text,
                                reply_markup=keyboard,
                                parse_mode="HTML"
                            )
                        except TelegramBadRequest as e:
                            if "message is not modified" in str(e):
                                pass
                            else:
                                raise
                else:
                    # No products either
                    text = "📂 <b>Каталог</b>\n\n😔 В данный момент товары не доступны."
                    keyboard = back_to_main_menu_keyboard()

                    if has_photo:
                        await callback.message.delete()
                        await callback.message.answer(
                            text,
                            reply_markup=keyboard,
                            parse_mode="HTML"
                        )
                    else:
                        try:
                            await callback.message.edit_text(
                                text,
                                reply_markup=keyboard,
                                parse_mode="HTML"
                            )
                        except TelegramBadRequest as e:
                            if "message is not modified" in str(e):
                                pass
                            else:
                                raise
        else:
            # "Магазин" category not found, show all root categories as fallback
            has_photo = callback.message.photo is not None and len(callback.message.photo) > 0

            text = "📂 <b>Каталог товаров</b>\n\nВыберите категорию:"
            keyboard = categories_keyboard(categories)

            if has_photo:
                await callback.message.delete()
                await callback.message.answer(
                    text,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
            else:
                try:
                    await callback.message.edit_text(
                        text,
                        reply_markup=keyboard,
                        parse_mode="HTML"
                    )
                except TelegramBadRequest as e:
                    if "message is not modified" in str(e):
                        pass
                    else:
                        raise

        await callback.answer()

    except Exception as e:
        logger.error(f"Error showing catalog: {e}")
        await callback.answer("Произошла ошибка при загрузке каталога", show_alert=True)


@router.callback_query(F.data.startswith("cat:"))
async def show_category(callback: CallbackQuery):
    """Show category contents (subcategories or products)"""
    try:
        category_id = int(callback.data.split(":")[1])

        # Get category details
        category = await opencart_service.get_category_details(category_id)

        if not category:
            await callback.answer("Категория не найдена", show_alert=True)
            return

        # Check if current message has photo
        has_photo = callback.message.photo is not None and len(callback.message.photo) > 0

        # Check for subcategories first
        subcategories = await opencart_service.get_subcategories(category_id)

        if subcategories:
            # Show subcategories
            text = f"📁 <b>{category['name']}</b>\n\nВыберите подкатегорию:"
            keyboard = categories_keyboard(subcategories, category['parent_id'])

            if has_photo:
                # Delete photo message and send text
                await callback.message.delete()
                await callback.message.answer(
                    text,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
            else:
                try:
                    await callback.message.edit_text(
                        text,
                        reply_markup=keyboard,
                        parse_mode="HTML"
                    )
                except TelegramBadRequest as e:
                    if "message is not modified" in str(e):
                        pass
                    else:
                        raise
        else:
            # Show products
            products = await opencart_service.get_products_by_category(
                category_id,
                limit=settings.PRODUCTS_PER_PAGE,
                offset=0
            )

            if not products:
                text = f"📁 <b>{category['name']}</b>\n\n😔 В этой категории пока нет товаров."
                keyboard = categories_keyboard([], category['parent_id'])

                if has_photo:
                    await callback.message.delete()
                    await callback.message.answer(
                        text,
                        reply_markup=keyboard,
                        parse_mode="HTML"
                    )
                else:
                    try:
                        await callback.message.edit_text(
                            text,
                            reply_markup=keyboard,
                            parse_mode="HTML"
                        )
                    except TelegramBadRequest as e:
                        if "message is not modified" in str(e):
                            pass
                        else:
                            raise
            else:
                text = f"📁 <b>{category['name']}</b>\n\nВыберите товар:"
                has_next = len(products) == settings.PRODUCTS_PER_PAGE
                keyboard = products_keyboard(products, category_id, 0, has_next, category['parent_id'])

                if has_photo:
                    await callback.message.delete()
                    await callback.message.answer(
                        text,
                        reply_markup=keyboard,
                        parse_mode="HTML"
                    )
                else:
                    try:
                        await callback.message.edit_text(
                            text,
                            reply_markup=keyboard,
                            parse_mode="HTML"
                        )
                    except TelegramBadRequest as e:
                        if "message is not modified" in str(e):
                            pass
                        else:
                            raise

        await callback.answer()

    except Exception as e:
        logger.error(f"Error showing category: {e}")
        await callback.answer("Произошла ошибка при загрузке категории", show_alert=True)


@router.callback_query(F.data.startswith("catpage:"))
async def show_category_page(callback: CallbackQuery):
    """Show specific page of products in category"""
    try:
        parts = callback.data.split(":")
        category_id = int(parts[1])
        page = int(parts[2])

        # Get category details
        category = await opencart_service.get_category_details(category_id)

        if not category:
            await callback.answer("Категория не найдена", show_alert=True)
            return

        # Get products for this page
        offset = page * settings.PRODUCTS_PER_PAGE
        products = await opencart_service.get_products_by_category(
            category_id,
            limit=settings.PRODUCTS_PER_PAGE,
            offset=offset
        )

        if not products:
            await callback.answer("Больше товаров нет", show_alert=True)
            return

        text = f"📁 <b>{category['name']}</b>\n\nВыберите товар:"
        has_next = len(products) == settings.PRODUCTS_PER_PAGE

        try:
            await callback.message.edit_text(
                text,
                reply_markup=products_keyboard(products, category_id, page, has_next, category['parent_id']),
                parse_mode="HTML"
            )
        except TelegramBadRequest as e:
            if "message is not modified" in str(e):
                pass
            else:
                raise

        await callback.answer()

    except Exception as e:
        logger.error(f"Error showing category page: {e}")
        await callback.answer("Произошла ошибка при загрузке страницы", show_alert=True)


@router.callback_query(F.data.startswith("prod:"))
async def show_product(callback: CallbackQuery):
    """Show product details"""
    try:
        product_id = int(callback.data.split(":")[1])

        # Get product details
        product = await opencart_service.get_product_details(product_id)

        if not product:
            await callback.answer("Товар не найден", show_alert=True)
            return

        # Generate product URL for OpenCart
        product_url = f"{settings.OPENCART_URL}/index.php?route=product/product&product_id={product_id}"

        # Format product card with URL for truncated descriptions
        text = format_product_card(product, product_url=product_url)

        # Prepare keyboard with product URL button
        keyboard = product_card_keyboard(
            product_id,
            product.get('category_id', 0),
            product.get('in_stock', False),
            product_url=product_url
        )

        # Check if current message has photo
        has_photo = callback.message.photo is not None and len(callback.message.photo) > 0

        # Try to send with image if available
        if product.get('image'):
            image_url = f"{settings.OPENCART_URL}/image/{product['image']}"

            try:
                if has_photo:
                    # Edit existing photo message
                    await callback.message.edit_media(
                        media=InputMediaPhoto(media=image_url, caption=text, parse_mode="HTML"),
                        reply_markup=keyboard
                    )
                else:
                    # Delete text message and send photo
                    await callback.message.delete()
                    await callback.message.answer_photo(
                        photo=image_url,
                        caption=text,
                        reply_markup=keyboard,
                        parse_mode="HTML"
                    )
            except Exception as img_error:
                logger.warning(f"Failed to send product image: {img_error}")
                # Fallback to text-only
                try:
                    await callback.message.edit_text(
                        text,
                        reply_markup=keyboard,
                        parse_mode="HTML"
                    )
                except TelegramBadRequest:
                    # Can't edit, send new message
                    await callback.message.delete()
                    await callback.message.answer(
                        text,
                        reply_markup=keyboard,
                        parse_mode="HTML"
                    )
        else:
            # No image, send text only
            try:
                if has_photo:
                    # Delete photo message and send text
                    await callback.message.delete()
                    await callback.message.answer(
                        text,
                        reply_markup=keyboard,
                        parse_mode="HTML"
                    )
                else:
                    # Edit existing text message
                    await callback.message.edit_text(
                        text,
                        reply_markup=keyboard,
                        parse_mode="HTML"
                    )
            except TelegramBadRequest as e:
                if "message is not modified" in str(e):
                    pass
                else:
                    raise

        await callback.answer()

    except Exception as e:
        logger.error(f"Error showing product: {e}")
        await callback.answer("Произошла ошибка при загрузке товара", show_alert=True)
