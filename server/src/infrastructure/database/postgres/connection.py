"""
Database Connection - SQLAlchemy Async
Single Responsibility: Manage database connections
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import text
from contextlib import asynccontextmanager
from src.config.settings import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()


def get_database_url() -> str:
    """
    Get async database URL
    Converts postgresql:// to postgresql+asyncpg://
    """
    db_url = settings.database_url
    if db_url.startswith("postgresql://"):
        return db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif db_url.startswith("postgresql+asyncpg://"):
        return db_url
    else:
        raise ValueError(f"Invalid database URL format: {db_url}")


# Create async engine
engine = create_async_engine(
    get_database_url(),
    echo=settings.debug,  # Log SQL queries in debug mode
    poolclass=NullPool,  # Use NullPool for async
    pool_pre_ping=True,  # Verify connections before using
    future=True
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


async def get_db() -> AsyncSession:
    """
    Dependency for getting database session
    Use this in FastAPI route dependencies
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context() -> AsyncSession:
    """
    Context manager for database session
    Use this for non-FastAPI contexts
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db():
    """
    Initialize database - create tables and extensions
    Should be called on application startup
    """
    from src.infrastructure.database.postgres.models import Base
    
    async with engine.begin() as conn:
        # Enable pgvector extension (if available)
        try:
            await conn.execute(
                text("CREATE EXTENSION IF NOT EXISTS vector")
            )
            logger.info("pgvector extension enabled")
        except Exception as e:
            logger.warning(
                f"Could not enable pgvector extension: {e}. "
                "Vector search features will not be available. "
                "To install pgvector, see: https://github.com/pgvector/pgvector"
            )
        
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("Database initialized successfully")


async def close_db():
    """
    Close database connections
    Should be called on application shutdown
    """
    await engine.dispose()
    logger.info("Database connections closed")
