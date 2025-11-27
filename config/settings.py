"""
Configuration settings for the WifiOBD Telegram Bot
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Telegram Bot
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [int(id.strip()) for id in os.getenv("ADMIN_IDS", "").split(",") if id.strip()]

# OpenCart API
OPENCART_URL = os.getenv("OPENCART_URL", "https://wifiobd.ru")
OPENCART_API_URL = os.getenv("OPENCART_API_URL", f"{OPENCART_URL}/index.php?route=api")
OPENCART_API_TOKEN = os.getenv("OPENCART_API_TOKEN", "")
OPENCART_API_USERNAME = os.getenv("OPENCART_API_USERNAME", "")
OPENCART_API_KEY = os.getenv("OPENCART_API_KEY", "")

# OpenCart Database (read-only access)
OPENCART_DB_HOST = os.getenv("OPENCART_DB_HOST", "localhost")
OPENCART_DB_PORT = int(os.getenv("OPENCART_DB_PORT", "3306"))
OPENCART_DB_NAME = os.getenv("OPENCART_DB_NAME", "opencart")
OPENCART_DB_USER = os.getenv("OPENCART_DB_USER", "")
OPENCART_DB_PASSWORD = os.getenv("OPENCART_DB_PASSWORD", "")

# Bot Database (PostgreSQL)
DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "wifiobd_bot_db")
DB_USER = os.getenv("DB_USER", "wifiobd_bot")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

# Database URLs
DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
OPENCART_DB_URL = f"mysql+aiomysql://{OPENCART_DB_USER}:{OPENCART_DB_PASSWORD}@{OPENCART_DB_HOST}:{OPENCART_DB_PORT}/{OPENCART_DB_NAME}"

# Redis
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

# YooMoney
YOOMONEY_TOKEN = os.getenv("YOOMONEY_TOKEN", "")
YOOMONEY_WALLET = os.getenv("YOOMONEY_WALLET", "")
YOOMONEY_CLIENT_ID = os.getenv("YOOMONEY_CLIENT_ID", "")

# Application settings
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Cart settings
CART_EXPIRE_DAYS = int(os.getenv("CART_EXPIRE_DAYS", "7"))

# Pagination
PRODUCTS_PER_PAGE = int(os.getenv("PRODUCTS_PER_PAGE", "10"))
CATEGORIES_PER_PAGE = int(os.getenv("CATEGORIES_PER_PAGE", "10"))

# Throttling (anti-spam)
THROTTLE_TIME = float(os.getenv("THROTTLE_TIME", "0.5"))  # seconds

# Logging
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)
