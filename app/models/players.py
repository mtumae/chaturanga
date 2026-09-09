import uuid
from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship, Enum, Column
from sqlalchemy import ForeignKey
from typing import Optional, List


class Player(SQLModel, table=True):
    __tablename__ = "players"
    # Clerk user ID as primary key (e.g. "user_2N9z...")
    id: str = Field(primary_key=True, max_length=64)

    # Synced user details from Clerk webhook
    username: str = Field(index=True, unique=True, min_length=3, max_length=30)
    email: str = Field(index=True, unique=True)
    avatar_url: Optional[str] = Field(default=None)

    # Application-specific status
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.now)
    last_online: Optional[datetime] = Field(default=None)

    # Clan Association
    clan_id: Optional[str] = Field(
        default=None,
        sa_column=Column(
            "clan_id",
            ForeignKey("clans.id", use_alter=True, name="fk_player_clan_id"),
            nullable=True,
        ),
    )
    ranking_id: Optional[str] = Field(
        default=None,
        sa_column=Column(
            "ranking_id",
            ForeignKey("rankings.id", use_alter=True, name="fk_player_ranking_id"),
            nullable=True,
        ),
    )
