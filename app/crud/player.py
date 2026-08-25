import uuid
from typing import Optional, List
from fastapi.exceptions import HTTPException
from sqlmodel import select

from sqlmodel import Field, SQLModel, Relationship, Enum, Column, Session
from app.models.game import Game
from app.models.players import Player
from app.models.rankings import Ranking
from datetime import datetime

    # __tablename__ = "players"

    # # Clerk user ID as primary key (e.g. "user_2N9z...")
    # id: str = Field(primary_key=True, max_length=64)

    # # Synced user details from Clerk webhook
    # username: str = Field(index=True, unique=True, min_length=3, max_length=30)
    # email: str = Field(index=True, unique=True)
    # avatar_url: Optional[str] = Field(default=None)

    # # Application-specific status
    # is_active: bool = Field(default=True)
    # is_bot: bool = Field(default=False)
    # created_at: datetime =  Field(default_factory=datetime.now().isoformat)
    # last_online: Optional[datetime] = Field(default=None)

    # # Clan Association
    # clan_id: Optional[uuid.UUID] = Field(default=None, foreign_key="clans.id")

    # # Relationships
    # rankings: List["Ranking"] = Relationship(back_populates="player")


async def create_player(
    session:Session,
    id:str, # Clerk ID
    username:str,
    email:str,
    avatar_url:str
):
    player = Player(
        id=id,
        username=username,
        email=email,
        avatar_url=avatar_url,
        is_active=True,
        last_online=datetime.now(),
        clan_id=None
    )

    ranking = Ranking(
        player_id=id
    )

    session.add(player)
    session.add(ranking)
    session.flush()
    session.commit()


async def update_activity(
    session:Session,
    id:str
):
    stmt = select(Player).where(Player.id==id)
    player = session.exec(stmt).first()
    if player:
        player.is_active = True
        session.add(player)
        session.commit()
        session.refresh(player)
    else:
        raise Exception("Player does not exist")
