from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from src.core.config import settings

engine = create_async_engine(
    str(settings.SQLALCHEMY_URL), echo=settings.SQLALCHEMY_ECHO
)
session_maker = async_sessionmaker(engine, class_=AsyncSession)
