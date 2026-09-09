import os

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import clan, rankings, players

load_dotenv()

database_url = os.getenv("DATABASE_URL")
if not database_url:
    database_url = "sqlite+aiosqlite:///database.db"
elif database_url.startswith("sqlite:///") and not database_url.startswith(
    "sqlite+aiosqlite:///"
):
    database_url = database_url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)

engine = create_async_engine(database_url)


async def create_db_and_tables():
    async with engine.begin() as connection:
        await connection.run_sync(SQLModel.metadata.create_all)


async def get_session():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session
