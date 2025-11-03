from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from .utils import is_async_url

def get_engines(database_url: str):
    if database_url.startswith("sqlite+aiosqlite") or database_url.startswith("postgresql+asyncpg"):
        async_engine = create_async_engine(database_url, future=True, echo=False)
        return async_engine, None
    else:
        engine = create_engine(database_url, future=True, echo=False)
        return None, engine

def get_session_factory(database_url: str):
    async_engine, engine = get_engines(database_url)
    if async_engine:
        return sessionmaker(async_engine, expire_on_commit=False, class_=AsyncSession)
    else:
        return sessionmaker(engine, autoflush=False, autocommit=False)
