import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from orbit.database.models import Base

DB_PATH = os.getenv("ORBIT_DB_PATH", "sqlite+aiosqlite:///orbit.db")

engine = create_async_engine(DB_PATH, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
