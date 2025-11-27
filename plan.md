# 🎯 Подробный план разработки Telegram-бота для интеграции с OpenCart

Создам архитектурный план разработки профессионального Telegram-бота для интеграции с магазином [wifiobd.ru](https://wifiobd.ru) (OpenCart 3.0.2.0) на базе вашей [платформы telegram-bots-platform](https://github.com/f2re/telegram-bots-platform).

## Архитектура и стек технологий

### Выбор технологий

- **Язык**: Python 3.11+
- **Фреймворк бота**: aiogram 3.x (современный, асинхронный)
- **База данных**: PostgreSQL (уже интегрирована в платформу)
- **Кэш**: Redis (для сессий и корзины)
- **API клиент**: aiohttp для асинхронных запросов
- **Платежи**: YooMoney API (библиотека yoomoney)
- **Контейнеризация**: Docker Compose


### Метод интеграции с OpenCart

**Рекомендация: Гибридный подход (API + прямой доступ к БД)**

**Обоснование:**

- **API OpenCart** - для критичных операций (создание заказов, обновление статусов)
- **Прямой доступ к БД** - для чтения данных (категории, товары) - быстрее и надежнее
- **Синхронизация через БД** - создание пользователей OpenCart при регистрации в боте


## Структура проекта

```
wifiobd-bot/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env
├── config/
│   ├── settings.py          # Конфигурация
│   └── opencart_db.py       # Настройки подключения к БД OpenCart
├── app/
│   ├── main.py              # Точка входа
│   ├── bot.py               # Инициализация бота
│   ├── handlers/            # Обработчики
│   │   ├── __init__.py
│   │   ├── start.py         # /start, главное меню
│   │   ├── catalog.py       # Просмотр категорий и товаров
│   │   ├── cart.py          # Корзина
│   │   ├── checkout.py      # Оформление заказа
│   │   ├── payment.py       # Оплата YooMoney
│   │   └── admin.py         # Админ-панель
│   ├── keyboards/           # Клавиатуры
│   │   ├── inline.py        # Inline кнопки
│   │   └── reply.py         # Reply клавиатуры (минимально)
│   ├── services/            # Бизнес-логика
│   │   ├── opencart.py      # Интеграция с OpenCart
│   │   ├── catalog.py       # Работа с каталогом
│   │   ├── cart.py          # Управление корзиной
│   │   ├── order.py         # Создание заказов
│   │   ├── user.py          # Управление пользователями
│   │   └── yoomoney.py      # Платежная интеграция
│   ├── database/            # Работа с БД
│   │   ├── models.py        # SQLAlchemy модели (своя БД)
│   │   ├── opencart_models.py # Модели для OpenCart БД
│   │   └── queries.py       # Запросы
│   ├── middlewares/         # Middleware
│   │   ├── throttling.py    # Антиспам
│   │   └── auth.py          # Проверка админа
│   ├── filters/             # Фильтры
│   │   └── admin.py         # Фильтр админа
│   ├── states/              # FSM состояния
│   │   ├── checkout.py      # Состояния оформления
│   │   └── admin.py         # Состояния админки
│   └── utils/               # Утилиты
│       ├── formatting.py    # Форматирование текста
│       ├── pagination.py    # Пагинация
│       └── logger.py        # Логирование
├── migrations/              # Alembic миграции
└── tests/                   # Тесты
```


## Детальный план разработки

### Этап 1: Подготовка инфраструктуры (1-2 дня)

#### 1.1 Настройка окружения

```bash
# На сервере с telegram-bots-platform
sudo ./add-bot.sh
# Название: wifiobd-bot
# Тип: Python bot с веб-интерфейсом
# Порт: автоматически
```


#### 1.2 Создание docker-compose.yml

```yaml
version: '3.8'
services:
  bot:
    build: .
    container_name: wifiobd_bot
    restart: unless-stopped
    env_file: .env
    volumes:
      - ./app:/app
      - ./logs:/logs
    networks:
      - bot_network
      - postgres_network
    depends_on:
      - redis
      - postgres

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    volumes:
      - redis_data:/data
    networks:
      - bot_network

  # PostgreSQL уже в платформе, подключаемся к нему

networks:
  bot_network:
  postgres_network:
    external: true
    name: platform_postgres_network

volumes:
  redis_data:
```


#### 1.3 Настройка доступа к БД OpenCart

- Создать read-only пользователя для чтения OpenCart БД
- Настроить VPN/SSH туннель если БД на другом сервере
- Протестировать подключение


### Этап 2: Базовая структура и интеграция с OpenCart (3-4 дня)

#### 2.1 Модели данных

**Собственная БД бота:**

```python
# database/models.py
class User(Base):
    id = Column(BigInteger, primary_key=True)  # Telegram ID
    opencart_customer_id = Column(Integer, nullable=True)
    username = Column(String(255))
    first_name = Column(String(255))
    phone = Column(String(20))
    email = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)

class Cart(Base):
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.id'))
    product_id = Column(Integer)  # OpenCart product_id
    quantity = Column(Integer)
    options = Column(JSON)  # Опции товара

class Order(Base):
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.id'))
    opencart_order_id = Column(Integer)
    yoomoney_payment_id = Column(String(255))
    amount = Column(Numeric(10, 2))
    status = Column(String(50))  # pending, paid, cancelled
    created_at = Column(DateTime)

class SupportTicket(Base):
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.id'))
    message = Column(Text)
    admin_response = Column(Text, nullable=True)
    status = Column(String(20))
    created_at = Column(DateTime)
```

**Модели OpenCart (read-only):**

```python
# database/opencart_models.py
class OCCategory(Base):
    __tablename__ = 'oc_category'
    category_id = Column(Integer, primary_key=True)
    parent_id = Column(Integer)
    sort_order = Column(Integer)
    status = Column(Boolean)

class OCCategoryDescription(Base):
    __tablename__ = 'oc_category_description'
    category_id = Column(Integer, primary_key=True)
    language_id = Column(Integer, primary_key=True)
    name = Column(String(255))

class OCProduct(Base):
    __tablename__ = 'oc_product'
    product_id = Column(Integer, primary_key=True)
    model = Column(String(64))
    price = Column(Numeric(15, 4))
    quantity = Column(Integer)
    status = Column(Boolean)
    image = Column(String(255))

class OCProductDescription(Base):
    __tablename__ = 'oc_product_description'
    product_id = Column(Integer, primary_key=True)
    name = Column(String(255))
    description = Column(Text)

class OCCustomer(Base):
    __tablename__ = 'oc_customer'
    customer_id = Column(Integer, primary_key=True)
    email = Column(String(96))
    telephone = Column(String(32))
```


#### 2.2 Сервис интеграции с OpenCart

```python
# services/opencart.py
class OpenCartService:
    def __init__(self):
        self.api_url = settings.OPENCART_API_URL
        self.api_token = settings.OPENCART_API_TOKEN
        self.db_engine = create_engine(settings.OPENCART_DB_URL)

    # Чтение через БД (быстрее)
    async def get_categories(self, parent_id=0):
        """Получить категории из БД OpenCart"""

    async def get_products_by_category(self, category_id, limit=10, offset=0):
        """Получить товары категории"""

    async def get_product_details(self, product_id):
        """Детальная информация о товаре"""

    # Запись через API (безопаснее)
    async def create_customer(self, user_data):
        """Создать клиента в OpenCart через API"""

    async def create_order(self, order_data):
        """Создать заказ через API"""

    async def update_order_status(self, order_id, status_id):
        """Обновить статус заказа"""
```


### Этап 3: Каталог и корзина (2-3 дня)

#### 3.1 Обработчики каталога

**UX/UI принципы:**

- ✅ Минимум текста, максимум структуры
- ✅ Эмодзи для навигации: 🏠 📁 🛒 💳 ⚙️
- ✅ Inline кнопки с callback_data
- ✅ Пагинация через кнопки ◀️ 1/5 ▶️
- ✅ Удаление предыдущих сообщений при навигации
- ✅ "Хлебные крошки" для понимания местоположения

```python
# handlers/catalog.py
@router.callback_query(F.data == "catalog")
async def show_categories(callback: CallbackQuery):
    """Показать корневые категории"""
    categories = await catalog_service.get_root_categories()

    keyboard = InlineKeyboardBuilder()
    for cat in categories:
        keyboard.button(
            text=f"📁 {cat.name}",
            callback_data=f"cat:{cat.id}"
        )
    keyboard.button(text="🏠 Главная", callback_data="start")
    keyboard.adjust(2)  # 2 кнопки в ряд

    await callback.message.edit_text(
        "📂 <b>Выберите категорию:</b>",
        reply_markup=keyboard.as_markup()
    )

@router.callback_query(F.data.startswith("cat:"))
async def show_category(callback: CallbackQuery):
    """Показать товары или подкатегории"""
    category_id = int(callback.data.split(":")[^1])

    # Проверка на подкатегории
    subcats = await catalog_service.get_subcategories(category_id)
    if subcats:
        # Показать подкатегории
        pass
    else:
        # Показать товары с пагинацией
        products = await catalog_service.get_products(
            category_id,
            page=0
        )
        await show_products(callback.message, products, category_id, 0)

async def show_products(message, products, category_id, page):
    """Отобразить товары с пагинацией"""
    keyboard = InlineKeyboardBuilder()

    for product in products:
        keyboard.button(
            text=f"{product.name} - {product.price}₽",
            callback_data=f"prod:{product.id}"
        )

    # Пагинация
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton(
            text="◀️",
            callback_data=f"catpage:{category_id}:{page-1}"
        ))
    nav_row.append(InlineKeyboardButton(
        text=f"{page+1}",
        callback_data="noop"
    ))
    if len(products) == 10:  # Полная страница
        nav_row.append(InlineKeyboardButton(
            text="▶️",
            callback_data=f"catpage:{category_id}:{page+1}"
        ))

    keyboard.row(*nav_row)
    keyboard.button(text="🔙 Назад", callback_data=f"cat:{category_id}")
    keyboard.adjust(1)

    await message.edit_text(
        "🛍 <b>Товары:</b>",
        reply_markup=keyboard.as_markup()
    )
```


#### 3.2 Карточка товара

```python
@router.callback_query(F.data.startswith("prod:"))
async def show_product(callback: CallbackQuery):
    """Детальная карточка товара"""
    product_id = int(callback.data.split(":")[^1])
    product = await catalog_service.get_product_details(product_id)

    # Отправить фото если есть
    if product.image:
        photo_url = f"{settings.OPENCART_URL}/image/{product.image}"

    text = f"""
<b>{product.name}</b>

{product.description[:300]}...

💰 <b>Цена:</b> {product.price}₽
📦 <b>В наличии:</b> {product.quantity} шт
"""

    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="➕ В корзину", callback_data=f"addcart:{product_id}")
    keyboard.button(text="🔙 Назад", callback_data=f"cat:{product.category_id}")
    keyboard.adjust(1)

    if product.image:
        await callback.message.delete()
        await callback.message.answer_photo(
            photo=photo_url,
            caption=text,
            reply_markup=keyboard.as_markup()
        )
    else:
        await callback.message.edit_text(
            text,
            reply_markup=keyboard.as_markup()
        )
```


#### 3.3 Корзина

```python
# services/cart.py
class CartService:
    def __init__(self, redis_client):
        self.redis = redis_client

    async def add_item(self, user_id, product_id, quantity=1):
        """Добавить товар в корзину"""
        key = f"cart:{user_id}"
        await self.redis.hincrby(key, product_id, quantity)
        await self.redis.expire(key, 86400 * 7)  # 7 дней

    async def get_cart(self, user_id):
        """Получить корзину"""
        key = f"cart:{user_id}"
        cart = await self.redis.hgetall(key)

        # Обогатить данными о товарах
        products = []
        total = 0
        for product_id, qty in cart.items():
            product = await catalog_service.get_product(product_id)
            products.append({
                "product": product,
                "quantity": int(qty),
                "subtotal": product.price * int(qty)
            })
            total += product.price * int(qty)

        return {"items": products, "total": total}
```


### Этап 4: Оформление заказа (2-3 дня)

#### 4.1 FSM для checkout

```python
# states/checkout.py
class CheckoutStates(StatesGroup):
    waiting_name = State()
    waiting_phone = State()
    waiting_address = State()
    waiting_comment = State()
    confirm = State()
```


#### 4.2 Обработчики checkout

```python
# handlers/checkout.py
@router.callback_query(F.data == "checkout")
async def start_checkout(callback: CallbackQuery, state: FSMContext):
    """Начать оформление заказа"""
    cart = await cart_service.get_cart(callback.from_user.id)

    if not cart["items"]:
        await callback.answer("🛒 Корзина пуста", show_alert=True)
        return

    # Проверить существование пользователя в OpenCart
    user = await user_service.get_user(callback.from_user.id)
    if not user.opencart_customer_id:
        # Создать клиента в OpenCart
        oc_customer = await opencart_service.create_customer({
            "firstname": user.first_name,
            "email": user.email or f"tg{user.id}@temp.com",
            "telephone": user.phone or ""
        })
        await user_service.update_opencart_id(user.id, oc_customer["customer_id"])

    await state.set_state(CheckoutStates.waiting_phone)
    await callback.message.edit_text(
        "📞 Введите ваш номер телефона:",
        reply_markup=skip_keyboard()
    )

@router.message(CheckoutStates.waiting_phone)
async def process_phone(message: Message, state: FSMContext):
    """Обработка телефона"""
    await state.update_data(phone=message.text)
    await state.set_state(CheckoutStates.waiting_address)

    await message.answer(
        "📍 Введите адрес доставки:",
        reply_markup=skip_keyboard()
    )

# ... остальные шаги

@router.callback_query(F.data == "confirm_order", CheckoutStates.confirm)
async def confirm_order(callback: CallbackQuery, state: FSMContext):
    """Подтверждение и создание заказа"""
    data = await state.get_data()
    cart = await cart_service.get_cart(callback.from_user.id)

    # Создать заказ в своей БД
    order = await order_service.create_order(
        user_id=callback.from_user.id,
        cart=cart,
        delivery_data=data
    )

    await state.clear()

    # Перейти к оплате
    await initiate_payment(callback, order)
```


### Этап 5: Интеграция YooMoney (2-3 дня)

#### 5.1 Настройка YooMoney

1. Зарегистрировать приложение на https://yoomoney.ru/myservices/new
2. Получить `client_id`
3. Выпустить токен с правами: `payment-p2p`, `operation-history`

#### 5.2 Сервис оплаты

```python
# services/yoomoney.py
from yoomoney import Client, Quickpay

class YooMoneyService:
    def __init__(self):
        self.client = Client(settings.YOOMONEY_TOKEN)
        self.wallet = settings.YOOMONEY_WALLET

    async def create_payment(self, order_id, amount):
        """Создать счет на оплату"""
        label = f"order_{order_id}_{int(time.time())}"

        quickpay = Quickpay(
            receiver=self.wallet,
            quickpay_form="shop",
            targets=f"Оплата заказа #{order_id}",
            paymentType="SB",
            sum=amount,
            label=label
        )

        # Сохранить label в БД заказа
        await order_service.update_payment_label(order_id, label)

        return {
            "payment_url": quickpay.redirected_url,
            "label": label
        }

    async def check_payment(self, label):
        """Проверить статус платежа"""
        history = self.client.operation_history(label=label)

        if history.operations:
            for operation in history.operations:
                if operation.status == "success":
                    return {
                        "status": "success",
                        "amount": operation.amount,
                        "datetime": operation.datetime
                    }

        return {"status": "pending"}
```


#### 5.3 Обработка оплаты

```python
# handlers/payment.py
async def initiate_payment(callback: CallbackQuery, order):
    """Инициировать оплату"""
    payment = await yoomoney_service.create_payment(
        order.id,
        order.amount
    )

    keyboard = InlineKeyboardBuilder()
    keyboard.button(
        text="💳 Оплатить",
        url=payment["payment_url"]
    )
    keyboard.button(
        text="✅ Проверить оплату",
        callback_data=f"checkpay:{order.id}"
    )
    keyboard.button(
        text="❌ Отменить",
        callback_data=f"cancelpay:{order.id}"
    )
    keyboard.adjust(1)

    await callback.message.edit_text(
        f"""
💰 <b>Заказ №{order.id}</b>

Сумма к оплате: <b>{order.amount}₽</b>

Нажмите кнопку ниже для оплаты через ЮMoney.
После оплаты вернитесь и нажмите "Проверить оплату".
""",
        reply_markup=keyboard.as_markup()
    )

@router.callback_query(F.data.startswith("checkpay:"))
async def check_payment(callback: CallbackQuery):
    """Проверить оплату"""
    order_id = int(callback.data.split(":")[^1])
    order = await order_service.get_order(order_id)

    payment_status = await yoomoney_service.check_payment(
        order.yoomoney_label
    )

    if payment_status["status"] == "success":
        # Обновить статус заказа
        await order_service.update_status(order_id, "paid")

        # Создать заказ в OpenCart
        oc_order = await opencart_service.create_order({
            "customer_id": order.user.opencart_customer_id,
            "products": order.items,
            "total": order.amount,
            "payment_method": "YooMoney",
            "shipping_address": order.address
        })

        await order_service.update_opencart_order_id(
            order_id,
            oc_order["order_id"]
        )

        await callback.message.edit_text(
            f"""
✅ <b>Оплата успешна!</b>

Заказ №{oc_order['order_id']} принят в обработку.
Ожидайте звонка менеджера.

<b>Спасибо за покупку!</b> 🎉
""",
            reply_markup=main_menu_keyboard()
        )
    else:
        await callback.answer(
            "⏳ Оплата еще не поступила. Попробуйте через минуту.",
            show_alert=True
        )
```


### Этап 6: Админ-панель (2-3 дня)

#### 6.1 Функционал админки

```python
# handlers/admin.py
@router.message(Command("admin"))
async def admin_menu(message: Message):
    """Админ меню"""
    if not await is_admin(message.from_user.id):
        return

    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="📋 Заказы", callback_data="admin:orders")
    keyboard.button(text="💬 Обращения", callback_data="admin:tickets")
    keyboard.button(text="👥 Пользователи", callback_data="admin:users")
    keyboard.button(text="📊 Статистика", callback_data="admin:stats")
    keyboard.adjust(2)

    await message.answer(
        "⚙️ <b>Админ-панель</b>",
        reply_markup=keyboard.as_markup()
    )

@router.callback_query(F.data == "admin:orders")
async def admin_orders(callback: CallbackQuery):
    """Список заказов"""
    orders = await order_service.get_recent_orders(limit=10)

    text = "<b>📋 Последние заказы:</b>\n\n"
    keyboard = InlineKeyboardBuilder()

    for order in orders:
        text += f"#{order.id} - {order.amount}₽ - {order.status}\n"
        keyboard.button(
            text=f"Заказ #{order.id}",
            callback_data=f"admin:order:{order.id}"
        )

    keyboard.button(text="🔙 Назад", callback_data="admin:menu")
    keyboard.adjust(1)

    await callback.message.edit_text(
        text,
        reply_markup=keyboard.as_markup()
    )

@router.callback_query(F.data.startswith("admin:order:"))
async def admin_order_details(callback: CallbackQuery):
    """Детали заказа"""
    order_id = int(callback.data.split(":")[^2])
    order = await order_service.get_order_full(order_id)

    text = f"""
<b>Заказ #{order.id}</b>

👤 Клиент: {order.user.first_name}
📞 Телефон: {order.phone}
📍 Адрес: {order.address}

💰 Сумма: {order.amount}₽
📦 Статус: {order.status}

<b>Товары:</b>
{format_order_items(order.items)}
"""

    keyboard = InlineKeyboardBuilder()
    if order.status == "paid":
        keyboard.button(
            text="❌ Отменить оплату",
            callback_data=f"admin:refund:{order.id}"
        )
    keyboard.button(
        text="💬 Написать клиенту",
        callback_data=f"admin:msg:{order.user_id}"
    )
    keyboard.button(text="🔙 Назад", callback_data="admin:orders")
    keyboard.adjust(1)

    await callback.message.edit_text(
        text,
        reply_markup=keyboard.as_markup()
    )

@router.callback_query(F.data.startswith("admin:refund:"))
async def admin_refund(callback: CallbackQuery, state: FSMContext):
    """Отмена платежа"""
    order_id = int(callback.data.split(":")[^2])

    # Обновить статус в БД
    await order_service.update_status(order_id, "refunded")

    # Обновить статус в OpenCart
    order = await order_service.get_order(order_id)
    if order.opencart_order_id:
        await opencart_service.update_order_status(
            order.opencart_order_id,
            7  # Cancelled
        )

    # Уведомить пользователя
    await bot.send_message(
        order.user_id,
        f"❌ Заказ #{order.id} отменен. Средства будут возвращены."
    )

    await callback.answer("✅ Платеж отменен", show_alert=True)

# Обращения в поддержку
@router.callback_query(F.data == "support")
async def create_support_ticket(callback: CallbackQuery, state: FSMContext):
    """Создать обращение"""
    await state.set_state(SupportStates.waiting_message)
    await callback.message.edit_text(
        "💬 Опишите вашу проблему:"
    )

@router.message(SupportStates.waiting_message)
async def save_support_ticket(message: Message, state: FSMContext):
    """Сохранить обращение"""
    ticket = await support_service.create_ticket(
        user_id=message.from_user.id,
        message=message.text
    )

    # Уведомить админов
    for admin_id in settings.ADMIN_IDS:
        await bot.send_message(
            admin_id,
            f"🆘 Новое обращение #{ticket.id}\n\n{message.text}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(
                    text="Ответить",
                    callback_data=f"admin:reply:{ticket.id}"
                )
            ]])
        )

    await message.answer(
        f"✅ Обращение #{ticket.id} создано.\nОжидайте ответа."
    )
    await state.clear()
```


### Этап 7: Тестирование и оптимизация (2-3 дня)

#### 7.1 Чек-лист тестирования

**Функциональное тестирование:**

- ✅ Навигация по каталогу (все уровни вложенности)
- ✅ Добавление товаров в корзину
- ✅ Изменение количества в корзине
- ✅ Процесс оформления заказа
- ✅ Успешная оплата через YooMoney (тестовый режим)
- ✅ Отмена платежа
- ✅ Создание пользователя в OpenCart
- ✅ Создание заказа в OpenCart
- ✅ Синхронизация статусов
- ✅ Работа админ-панели
- ✅ Ответы на обращения
- ✅ Антиспам (throttling)

**Интеграционное тестирование:**

- ✅ Корректность данных из OpenCart БД
- ✅ API вызовы к OpenCart
- ✅ Проверка платежей YooMoney
- ✅ Создание заказов с полной структурой

**Нагрузочное тестирование:**

- ✅ 100+ одновременных пользователей
- ✅ Работа Redis при высокой нагрузке


#### 7.2 Оптимизация

```python
# Кэширование каталога
@lru_cache(maxsize=128)
async def get_cached_categories():
    """Кэш категорий на 1 час"""
    return await catalog_service.get_categories()

# Batch операции
async def get_products_batch(product_ids):
    """Получить несколько товаров за один запрос"""
    query = select(OCProduct).where(
        OCProduct.product_id.in_(product_ids)
    )
    return await db.execute(query)
```


### Этап 8: Деплой и мониторинг (1 день)

#### 8.1 Деплой

```bash
# На сервере
cd /opt/telegram-bots-platform/bots/wifiobd-bot
docker compose up -d --build

# Проверка логов
docker compose logs -f bot

# Проверка статуса
./monitor-status.sh
```


#### 8.2 Настройка мониторинга

- Добавить метрики в Prometheus:
    - Количество заказов в час
    - Среднее время отклика бота
    - Количество ошибок API
    - Успешность платежей
- Создать dashboard в Grafana с:
    - Графиками продаж
    - Активными пользователями
    - Статусами заказов


## Переменные окружения

```ini
# .env
BOT_TOKEN=your_telegram_bot_token
ADMIN_IDS=123456789,987654321

# OpenCart API
OPENCART_URL=https://wifiobd.ru
OPENCART_API_URL=https://wifiobd.ru/index.php?route=api
OPENCART_API_TOKEN=your_opencart_api_token

# OpenCart Database (read-only)
OPENCART_DB_HOST=localhost
OPENCART_DB_PORT=3306
OPENCART_DB_NAME=opencart
OPENCART_DB_USER=readonly_user
OPENCART_DB_PASSWORD=secure_password

# Bot Database (PostgreSQL)
DB_HOST=postgres
DB_PORT=5432
DB_NAME=wifiobd_bot_db
DB_USER=wifiobd_bot
DB_PASSWORD=generated_password

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# YooMoney
YOOMONEY_TOKEN=your_yoomoney_token
YOOMONEY_WALLET=410011234567890
YOOMONEY_CLIENT_ID=your_client_id
```


## Итоговая оценка сроков

- **Этап 1**: Инфраструктура - 2 дня
- **Этап 2**: Интеграция OpenCart - 4 дня
- **Этап 3**: Каталог и корзина - 3 дня
- **Этап 4**: Оформление заказа - 3 дня
- **Этап 5**: YooMoney - 3 дня
- **Этап 6**: Админ-панель - 3 дня
- **Этап 7**: Тестирование - 3 дня
- **Этап 8**: Деплой - 1 день

**Итого: 22 рабочих дня (~1 месяц)**

## Рекомендации по безопасности

- ✅ Использовать read-only доступ к БД OpenCart
- ✅ Валидация всех пользовательских данных
- ✅ Rate limiting (антиспам)
- ✅ Хранение токенов в переменных окружения
- ✅ HTTPS для всех API запросов
- ✅ Логирование всех критичных операций
- ✅ Бэкапы БД ежедневно

Этот план обеспечивает профессиональную, надежную интеграцию с отличным UX и полным контролем над бизнес-процессами.
