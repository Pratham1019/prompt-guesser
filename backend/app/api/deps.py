from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.database import SessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that yields a database session and ensures it is closed after use.
    """
    async with SessionLocal() as session:
        yield session
