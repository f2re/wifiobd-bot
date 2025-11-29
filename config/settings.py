"""
Configuration settings for VK bot
"""
import os
from typing import List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings:
    """Application settings"""

    # VK Bot
    VK_TOKEN: str = os.getenv("VK_TOKEN", "")
    VK_GROUP_ID: int = int(os.getenv("VK_GROUP_ID", "0"))
    VK_API_VERSION: str = os.getenv("VK_API_VERSION", "5.131")
    VK_CONFIRMATION_CODE: str = os.getenv("VK_CONFIRMATION_CODE", "")
    
    # Admin users (VK IDs)
    ADMIN_IDS: List[int] = [
        int(id.strip()) 
        for id in os.getenv("ADMIN_IDS", "").split(",") 
        if id.strip()
    ]

    # OpenCart
    OPENCART_URL: str = os.getenv("OPENCART_URL", "https://wifiobd.ru")
    OPENCART_API_USERNAME: str = os.getenv("OPENCART_API_USERNAME", "")
    OPENCART_API_KEY: str = os.getenv("OPENCART_API_KEY", "")

    # OpenCart Database (Read-Only)
    OPENCART_DB_HOST: str = os.getenv("OPENCART_DB_HOST", "localhost")
    OPENCART_DB_PORT: int = int(os.getenv("OPENCART_DB_PORT", "3306"))
    OPENCART_DB_NAME: str = os.getenv("OPENCART_DB_NAME", "opencart")
    OPENCART_DB_USER: str = os.getenv("OPENCART_DB_USER", "")
    OPENCART_DB_PASSWORD: str = os.getenv("OPENCART_DB_PASSWORD", "")

    # Bot Database (PostgreSQL)
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_NAME: str = os.getenv("DB_NAME", "wifiobd_bot_db")
    DB_USER: str = os.getenv("DB_USER", "wifiobd_bot")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")

    @property
    def DATABASE_URL(self) -> str:
        """PostgreSQL connection URL"""
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    # Redis
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")

    @property
    def REDIS_URL(self) -> str:
        """Redis connection URL"""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # YooKassa Payment
    YOOKASSA_SHOP_ID: str = os.getenv("YOOKASSA_SHOP_ID", "")
    YOOKASSA_SECRET_KEY: str = os.getenv("YOOKASSA_SECRET_KEY", "")

    # Application
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Cart Settings
    CART_EXPIRE_DAYS: int = int(os.getenv("CART_EXPIRE_DAYS", "7"))

    # Pagination
    PRODUCTS_PER_PAGE: int = int(os.getenv("PRODUCTS_PER_PAGE", "10"))
    CATEGORIES_PER_PAGE: int = int(os.getenv("CATEGORIES_PER_PAGE", "10"))

    # Throttling
    THROTTLE_TIME: float = float(os.getenv("THROTTLE_TIME", "0.5"))

    def validate(self) -> bool:
        """Validate required settings"""
        required = [
            (self.VK_TOKEN, "VK_TOKEN"),
            (self.VK_GROUP_ID, "VK_GROUP_ID"),
            (self.DB_PASSWORD, "DB_PASSWORD"),
            (self.OPENCART_DB_HOST, "OPENCART_DB_HOST"),
            (self.YOOKASSA_SHOP_ID, "YOOKASSA_SHOP_ID"),
            (self.YOOKASSA_SECRET_KEY, "YOOKASSA_SECRET_KEY"),
        ]

        missing = [name for value, name in required if not value]
        
        if missing:
            raise ValueError(f"Missing required settings: {', '.join(missing)}")
        
        return True


# Create global settings instance
settings = Settings()

# Validate on import
if not os.getenv("SKIP_VALIDATION"):
    settings.validate()
