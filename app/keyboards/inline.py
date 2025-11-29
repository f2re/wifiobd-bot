"""
VK Inline keyboards for bot navigation
"""
from vkbottle import Keyboard, KeyboardButtonColor, Callback, Text, OpenLink
from typing import List, Optional


class VKKeyboards:
    """VK Keyboard builder for bot"""

    @staticmethod
    def main_menu() -> str:
        """Main menu keyboard"""
        keyboard = Keyboard(one_time=False, inline=False)
        keyboard.add(Text("🛍 Каталог"), color=KeyboardButtonColor.PRIMARY)
        keyboard.add(Text("🛒 Корзина"), color=KeyboardButtonColor.PRIMARY)
        keyboard.row()
        keyboard.add(Text("📦 Мои заказы"), color=KeyboardButtonColor.SECONDARY)
        keyboard.add(Text("💬 Поддержка"), color=KeyboardButtonColor.SECONDARY)
        keyboard.row()
        keyboard.add(Text("ℹ️ Помощь"), color=KeyboardButtonColor.SECONDARY)
        return keyboard.get_json()

    @staticmethod
    def catalog_categories(categories: List[dict]) -> str:
        """Catalog categories keyboard"""
        keyboard = Keyboard(one_time=False, inline=True)
        
        for i, category in enumerate(categories):
            keyboard.add(
                Callback(
                    label=category['name'][:40],  # VK limit
                    payload={'action': 'category', 'id': category['id']}
                )
            )
            # Two buttons per row
            if (i + 1) % 2 == 0:
                keyboard.row()
        
        keyboard.row()
        keyboard.add(Callback(label="🔙 Назад", payload={'action': 'back_to_menu'}))
        return keyboard.get_json()

    @staticmethod
    def product_actions(product_id: int, in_cart: bool = False) -> str:
        """Product actions keyboard"""
        keyboard = Keyboard(one_time=False, inline=True)
        
        if in_cart:
            keyboard.add(
                Callback(
                    label="➖ Удалить из корзины",
                    payload={'action': 'remove_from_cart', 'product_id': product_id}
                ),
                color=KeyboardButtonColor.NEGATIVE
            )
        else:
            keyboard.add(
                Callback(
                    label="➕ В корзину",
                    payload={'action': 'add_to_cart', 'product_id': product_id}
                ),
                color=KeyboardButtonColor.POSITIVE
            )
        
        keyboard.row()
        keyboard.add(
            Callback(
                label="🔙 К категории",
                payload={'action': 'back_to_category'}
            )
        )
        keyboard.add(
            Callback(
                label="📋 Каталог",
                payload={'action': 'catalog'}
            )
        )
        return keyboard.get_json()

    @staticmethod
    def cart_actions(has_items: bool = True) -> str:
        """Cart actions keyboard"""
        keyboard = Keyboard(one_time=False, inline=True)
        
        if has_items:
            keyboard.add(
                Callback(
                    label="✅ Оформить заказ",
                    payload={'action': 'checkout'}
                ),
                color=KeyboardButtonColor.POSITIVE
            )
            keyboard.row()
            keyboard.add(
                Callback(
                    label="🗑 Очистить корзину",
                    payload={'action': 'clear_cart'}
                ),
                color=KeyboardButtonColor.NEGATIVE
            )
        
        keyboard.row()
        keyboard.add(
            Callback(
                label="🔙 Главное меню",
                payload={'action': 'main_menu'}
            )
        )
        return keyboard.get_json()

    @staticmethod
    def checkout_confirm() -> str:
        """Checkout confirmation keyboard"""
        keyboard = Keyboard(one_time=False, inline=True)
        keyboard.add(
            Callback(
                label="✅ Подтвердить",
                payload={'action': 'confirm_order'}
            ),
            color=KeyboardButtonColor.POSITIVE
        )
        keyboard.add(
            Callback(
                label="❌ Отменить",
                payload={'action': 'cancel_checkout'}
            ),
            color=KeyboardButtonColor.NEGATIVE
        )
        return keyboard.get_json()

    @staticmethod
    def payment_method() -> str:
        """Payment method selection keyboard"""
        keyboard = Keyboard(one_time=False, inline=True)
        keyboard.add(
            Callback(
                label="💳 Оплатить картой (YooKassa)",
                payload={'action': 'pay_yookassa'}
            ),
            color=KeyboardButtonColor.PRIMARY
        )
        keyboard.row()
        keyboard.add(
            Callback(
                label="🔙 Назад",
                payload={'action': 'back_to_cart'}
            )
        )
        return keyboard.get_json()

    @staticmethod
    def admin_menu() -> str:
        """Admin panel keyboard"""
        keyboard = Keyboard(one_time=False, inline=True)
        keyboard.add(
            Callback(label="📋 Заказы", payload={'action': 'admin_orders'})
        )
        keyboard.add(
            Callback(label="💬 Обращения", payload={'action': 'admin_tickets'})
        )
        keyboard.row()
        keyboard.add(
            Callback(label="👥 Пользователи", payload={'action': 'admin_users'})
        )
        keyboard.add(
            Callback(label="📊 Статистика", payload={'action': 'admin_stats'})
        )
        keyboard.row()
        keyboard.add(
            Callback(label="📢 Рассылка", payload={'action': 'admin_broadcast'})
        )
        return keyboard.get_json()

    @staticmethod
    def pagination(current_page: int, total_pages: int, callback_prefix: str) -> str:
        """Pagination keyboard"""
        keyboard = Keyboard(one_time=False, inline=True)
        
        if current_page > 1:
            keyboard.add(
                Callback(
                    label="⬅️ Назад",
                    payload={'action': f'{callback_prefix}_page', 'page': current_page - 1}
                )
            )
        
        keyboard.add(
            Callback(
                label=f"{current_page}/{total_pages}",
                payload={'action': 'current_page'}
            )
        )
        
        if current_page < total_pages:
            keyboard.add(
                Callback(
                    label="➡️ Вперед",
                    payload={'action': f'{callback_prefix}_page', 'page': current_page + 1}
                )
            )
        
        return keyboard.get_json()

    @staticmethod
    def back_button(action: str = 'back') -> str:
        """Simple back button"""
        keyboard = Keyboard(one_time=False, inline=True)
        keyboard.add(
            Callback(
                label="🔙 Назад",
                payload={'action': action}
            )
        )
        return keyboard.get_json()

    @staticmethod
    def url_button(label: str, url: str) -> str:
        """URL button keyboard"""
        keyboard = Keyboard(one_time=False, inline=True)
        keyboard.add(OpenLink(label=label, link=url))
        return keyboard.get_json()
