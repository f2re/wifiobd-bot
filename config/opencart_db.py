"""
OpenCart database connection configuration
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from config.settings import OPENCART_DB_URL

# Create async engine for OpenCart database (read-only)
opencart_engine = create_async_engine(
    OPENCART_DB_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

# Session factory for OpenCart database
OpenCartSessionLocal = sessionmaker(
    opencart_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_opencart_db():
    """Dependency for getting OpenCart database session"""
    async with OpenCartSessionLocal() as session:
        yield session
