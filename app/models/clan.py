import uuid
from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship, Enum, Column, Integer
from typing import Optional, List



class Clan(SQLModel, table=True):
    __tablename__ = "clans"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=64)
    ranking: int = Field(default=0)
    description: Optional[str] = Field(default=None, max_length=255)
    name: str = Field(index=True, unique=True, min_length=3, max_length=30)
    profile_url: Optional[str] = Field(default=None)
    created_by: Optional[str] = Field(default=None, foreign_key="players.id")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
