from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

# Configure connection arguments
# If using SQLite, check_same_thread must be disabled for multi-threaded access in development
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False,
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
