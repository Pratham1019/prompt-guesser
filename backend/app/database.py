from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

# Configure async engine with connection pooling options
engine_kwargs: dict[str, Any] = {"echo": False}
if settings.DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # Production settings for Supabase PostgreSQL connection pool
    engine_kwargs.update(
        {
            "pool_size": 10,
            "max_overflow": 20,
            "pool_recycle": 1800,
            "pool_pre_ping": True,
        }
    )

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    **engine_kwargs,
)

# Session factory for generating AsyncSession instances
SessionLocal = async_sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_db_context():
    """
    Asymmetric context manager for acquiring database sessions.
    Useful for scripts, tasks, and middlewares outside of normal request contexts.
    """
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
