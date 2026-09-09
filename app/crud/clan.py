import uuid
from typing import Optional, List
from fastapi.exceptions import HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.clan import Clan
from app.models.players import Player


# __tablename__ = "clans"

# id: str = Field(primary_key=True, max_length=64)
# # ranking = ??
# description: Optional[str] = Field(default=None, max_length=255)
# name: str = Field(index=True, unique=True, min_length=3, max_length=30)
# profile_url: Optional[str] = Field(default=None)
# created_at: datetime =  Field(default_factory=datetime.now().isoformat)
# updated_at: datetime =  Field(default_factory=datetime.now().isoformat)
# # Relationships
# members: List["Player"] = Relationship(back_populates="clan")


async def create_clan(
    session: AsyncSession,
    name: str,
    profile_url: Optional[str],
    user_id: uuid.UUID,
    description: str,
    # profile_url:Optional[str],
) -> Clan:
    clan = Clan(
        name=name,
        profile_url=profile_url if not None else "",
        created_by=user_id,
        description=description,
    )
    session.add(clan)
    await session.flush()

    return clan


async def join_clan(session: AsyncSession, user_id: uuid.UUID, clan_id: uuid.UUID):
    player = await session.get(Player, user_id)
    if player and player.clan_id:
        raise Exception("Player is already in a clan.")
    elif player and player.clan_id is None:
        player.clan_id = clan_id
        session.add(player)
        await session.commit()
        return True


async def leave_clan(
    session: AsyncSession,
    user_id: uuid.UUID,
):
    player = await session.get(Player, user_id)
    if player and player.clan_id is None:
        raise Exception("Player is not part of a clan.")
    elif player and player.clan_id:
        player.clan_id = None
        session.add(player)
        await session.commit()
        return True


async def remove_player(
    session: AsyncSession,
    user_id: uuid.UUID,
):
    player = await session.get(Player, user_id)
    if player and player.clan_id:
        player.clan_id = None
        session.add(player)
        await session.commit()
        return True


async def get_clan(
    session: AsyncSession,
    clan_id: uuid.UUID,
):
    stmt = select(Clan).where(Clan.id == clan_id)
    res = await session.exec(stmt)
    return res


async def get_top_clan(session: AsyncSession):
    stmt = select(Clan).order_by(Clan.ranking).limit(10)
    res = await session.exec(stmt)
    return res
