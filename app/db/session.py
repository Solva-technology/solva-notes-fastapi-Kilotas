import asyncio
import logging
from sqlite3 import OperationalError
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings
from app.db.models import Base

engine = create_async_engine(settings.DATABASE_URL, echo=False, pool_pre_ping=True)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


logger = logging.getLogger(__name__)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def init_db(retries: int = 30, delay: float = 1.0) -> None:
    """Надёжное создание схемы с ретраями."""
    for i in range(1, retries + 1):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("DB init OK")
            return
        except OperationalError as e:
            logger.warning(f"[init_db] try {i}/{retries}: DB not ready: {e}")
        except Exception as e:
            logger.warning(f"[init_db] try {i}/{retries}: {e}")
        await asyncio.sleep(delay)
    raise RuntimeError(f"DB not ready after {retries} attempts")
