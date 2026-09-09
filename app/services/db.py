from app.models import clan, rankings, players
import os
from dotenv import load_dotenv
from sqlalchemy import text
from sqlmodel import Session, create_engine, SQLModel

load_dotenv()

database_url = os.getenv("DATABASE_URL")
engine = create_engine(database_url if database_url else "sqlite:///database.db")


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def check_database_connection():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))


def get_session():
    with Session(engine) as session:
        yield session
