"""
Shopping cart handlers
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery

from app.services.cart import cart_service
from app.services.opencart import opencart_service
from app.keyboards.inline import cart_keyboard, back_to_main_menu_keyboard
from app.utils.logger import get_logger
from app.utils.formatting import format_cart_summary

logger = get_logger(__name__)

router = Router()


@router.callback_query(F.data.startswith("addcart:"))
async def add_to_cart(callback: CallbackQuery):
    """Add product to cart"""
    try:
        product_id = int(callback.data.split(":")[1])
        user_id = callback.from_user.id

        # Get product details to verify it exists and is in stock
        product = await opencart_service.get_product_details(product_id)

        if not product:
            await callback.answer("❌ Товар не найден", show_alert=True)
            return

        if not product.get('in_stock', False):
            await callback.answer("❌ Товар отсутствует на складе", show_alert=True)
            return

        # Add to cart
        success = await cart_service.add_item(user_id, product_id, quantity=1)

        if success:
            # Get cart count
            count = await cart_service.get_item_count(user_id)
            await callback.answer(
                f"✅ Товар добавлен в корзину!\n🛒 Товаров в корзине: {count}",
                show_alert=False
            )
        else:
            await callback.answer("❌ Не удалось добавить товар в корзину", show_alert=True)

    except Exception as e:
        logger.error(f"Error adding to cart: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)


@router.callback_query(F.data == "cart")
async def show_cart(callback: CallbackQuery):
    """Show shopping cart"""
    try:
        user_id = callback.from_user.id

        # Get cart
        cart = await cart_service.get_cart(user_id)

        if not cart["items"]:
            text = "🛒 <b>Ваша корзина пуста</b>\n\nДобавьте товары из каталога."
            keyboard = back_to_main_menu_keyboard()
        else:
            text = format_cart_summary(cart)
            keyboard = cart_keyboard(has_items=True)

        await callback.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )

        await callback.answer()

    except Exception as e:
        logger.error(f"Error showing cart: {e}")
        await callback.answer("Произошла ошибка при загрузке корзины", show_alert=True)


@router.callback_query(F.data.startswith("cart_inc:"))
async def cart_increase_quantity(callback: CallbackQuery):
    """Increase product quantity in cart"""
    try:
        product_id = int(callback.data.split(":")[1])
        user_id = callback.from_user.id

        # Get current cart
        cart = await cart_service.get_cart(user_id)

        # Find the item
        current_qty = 0
        for item in cart["items"]:
            if item["product_id"] == product_id:
                current_qty = item["quantity"]
                break

        if current_qty == 0:
            await callback.answer("Товар не найден в корзине", show_alert=True)
            return

        # Increase quantity
        new_qty = current_qty + 1
        await cart_service.update_quantity(user_id, product_id, new_qty)

        # Refresh cart display
        cart = await cart_service.get_cart(user_id)
        text = format_cart_summary(cart)

        await callback.message.edit_text(
            text,
            reply_markup=cart_keyboard(has_items=True),
            parse_mode="HTML"
        )

        await callback.answer(f"✅ Количество увеличено: {new_qty}")

    except Exception as e:
        logger.error(f"Error increasing quantity: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)


@router.callback_query(F.data.startswith("cart_dec:"))
async def cart_decrease_quantity(callback: CallbackQuery):
    """Decrease product quantity in cart"""
    try:
        product_id = int(callback.data.split(":")[1])
        user_id = callback.from_user.id

        # Get current cart
        cart = await cart_service.get_cart(user_id)

        # Find the item
        current_qty = 0
        for item in cart["items"]:
            if item["product_id"] == product_id:
                current_qty = item["quantity"]
                break

        if current_qty == 0:
            await callback.answer("Товар не найден в корзине", show_alert=True)
            return

        # Decrease quantity
        new_qty = current_qty - 1

        if new_qty <= 0:
            # Remove from cart
            await cart_service.remove_item(user_id, product_id)
            await callback.answer("🗑 Товар удален из корзины")
        else:
            await cart_service.update_quantity(user_id, product_id, new_qty)
            await callback.answer(f"✅ Количество уменьшено: {new_qty}")

        # Refresh cart display
        cart = await cart_service.get_cart(user_id)

        if not cart["items"]:
            text = "🛒 <b>Ваша корзина пуста</b>\n\nДобавьте товары из каталога."
            keyboard = back_to_main_menu_keyboard()
        else:
            text = format_cart_summary(cart)
            keyboard = cart_keyboard(has_items=True)

        await callback.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )

    except Exception as e:
        logger.error(f"Error decreasing quantity: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)


@router.callback_query(F.data.startswith("cart_remove:"))
async def cart_remove_item(callback: CallbackQuery):
    """Remove item from cart"""
    try:
        product_id = int(callback.data.split(":")[1])
        user_id = callback.from_user.id

        # Remove from cart
        success = await cart_service.remove_item(user_id, product_id)

        if success:
            await callback.answer("🗑 Товар удален из корзины")
        else:
            await callback.answer("Товар не найден в корзине", show_alert=True)

        # Refresh cart display
        cart = await cart_service.get_cart(user_id)

        if not cart["items"]:
            text = "🛒 <b>Ваша корзина пуста</b>\n\nДобавьте товары из каталога."
            keyboard = back_to_main_menu_keyboard()
        else:
            text = format_cart_summary(cart)
            keyboard = cart_keyboard(has_items=True)

        await callback.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )

    except Exception as e:
        logger.error(f"Error removing item: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)


@router.callback_query(F.data == "clear_cart")
async def clear_cart(callback: CallbackQuery):
    """Clear entire cart"""
    try:
        user_id = callback.from_user.id

        # Clear cart
        await cart_service.clear_cart(user_id)

        text = "🛒 <b>Корзина очищена</b>\n\nВсе товары удалены из корзины."

        await callback.message.edit_text(
            text,
            reply_markup=back_to_main_menu_keyboard(),
            parse_mode="HTML"
        )

        await callback.answer("🗑 Корзина очищена")

    except Exception as e:
        logger.error(f"Error clearing cart: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)
