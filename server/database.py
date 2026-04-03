"""
SQLAlchemy 비동기 엔진 & 세션 설정.
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from config import DATABASE_URL


engine = create_async_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    """FastAPI Depends로 사용하는 DB 세션 의존성."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def create_tables():
    """앱 시작 시 테이블 자동 생성."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
