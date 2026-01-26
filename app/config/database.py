from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.config.settings import settings
from app.config.config_manager import config_manager

# Get database configuration from config manager
db_config = config_manager.get_database_config()

engine = create_async_engine(
    settings.database_url,
    pool_size=db_config["pool_size"],
    max_overflow=db_config["max_overflow"],
    pool_pre_ping=db_config["pool_pre_ping"],
    echo=db_config["echo"],
)

AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()