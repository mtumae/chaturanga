import uuid
from typing import Literal, Optional, List
from fastapi.exceptions import HTTPException
from pydantic import BaseModel, Field, AliasChoices
from sqlmodel import select

from sqlmodel import SQLModel, Relationship, Enum, Column, Session
from app.models.game import Game
from app.models.players import Player
from app.models.rankings import Ranking
from datetime import datetime


class PlayerRatingRequest(BaseModel):
    player_id: str = Field(validation_alias=AliasChoices("playerId", "player_id"))
    bot_tier: int = Field(validation_alias=AliasChoices("botTier", "bot_tier"))
    outcome: Literal["w", "l", "d"]


async def create_player(
    session: Session,
    id: str,  # Clerk ID
    username: str,
    email: str,
    avatar_url: str,
):
    player = Player(
        id=id,
        username=username,
        email=email,
        avatar_url=avatar_url,
        is_active=True,
        last_online=datetime.now(),
        clan_id=None,
    )

    ranking = Ranking(player_id=id)

    session.add(player)
    session.add(ranking)
    session.flush()
    session.commit()


async def update_activity(session: Session, id: str):
    stmt = select(Player).where(Player.id == id)
    player = session.exec(stmt).first()
    if player:
        player.is_active = True
        session.add(player)
        session.commit()
        session.refresh(player)
    else:
        raise Exception("Player does not exist")


def get_elo_rating(
    # this is for games against a bot
    player_rating: float,
    bot_tier: int,  # 1 to 10
    outcome: float,  # 1.0 = win, 0.5 = draw, 0.0 = loss
    k_factor: float = 32.0,
) -> float:
    # Derive bot rating directly from tier: Tier 1 = 800, Tier 10 = 2400
    bot_rating = 800 + (bot_tier - 1) * 177.78

    # Standard Elo expectation
    expected_score = 1.0 / (1.0 + 10.0 ** ((bot_rating - player_rating) / 400.0))
    new_rating = player_rating + k_factor * (outcome - expected_score)

    return round(new_rating, 2)


def update_player_rating(
    session: Session,
    player_id: str,
    bot_tier: int,
    outcome: Literal["w", "l", "d"],
) -> Ranking:
    outcome_scores = {"w": 1.0, "l": 0.0, "d": 0.5}
    try:
        outcome_score = outcome_scores[outcome]
    except KeyError as exc:
        raise ValueError("outcome must be 'w', 'l', or 'd'") from exc

    stmt = select(Player).where(Player.id == player_id)
    player = session.exec(stmt).first()

    if player is None:
        raise ValueError("Player does not exist")

    stmt2 = select(Ranking).where(Ranking.id == player.ranking_id)
    rank = session.exec(stmt2).first()
    if rank is None:
        raise ValueError("Player ranking does not exist")

    new_rating = get_elo_rating(rank.rating, bot_tier, outcome_score)
    rank.peak_rating = max(new_rating, rank.peak_rating)
    rank.rating = new_rating
    if outcome == "w":
        rank.wins += 1
    elif outcome == "l":
        rank.losses += 1
    else:
        rank.draws += 1
    rank.updated_at = datetime.now()

    session.commit()
    session.refresh(rank)
    return rank
