from typing import Optional, List, Literal
from fastapi.exceptions import HTTPException
from pydantic import AliasChoices, Field, BaseModel
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import SQLModel, Relationship, Enum, Column, Session
from app.crud.player import PlayerRatingRequest
from app.models.game import Game
from app.models.players import Player
from datetime import datetime
from app.crud.player import update_player_rating


# class GameStatus(str, Enum):
#     PENDING = "pending"
#     COMPLETED = "completed"
#     ABANDONED = "abandoned"


def create_game(
    session: Session,
    player_id: str,
):
    game = Game(
        fen=None,
        moves_history=[],
        pgn=None,
        created_by=player_id,
        winner_id=None,
        termination_reason=None,
        status="created",
    )

    session.add(game)
    session.flush()
    session.commit()


def save_game(
    session: Session,
    game_id: str,
    player_id: str,
    fen: str,
    moves_history: list[str],
    pgn: str,
    status: Literal["completed", "pending", "abandoned"],
):
    stmt = select(Game).where(Game.id == game_id)
    game = session.exec(stmt).first()
    if game is None:
        raise Exception("Game not found")

    if game.created_by != player_id:
        raise Exception("Player is attempted to save a game they did not create.")
    game.fen = fen
    game.moves_history = moves_history
    game.updated_at = datetime.now()
    game.pgn = pgn
    game.status = status

    session.add(game)
    session.commit()
    session.refresh(game)


def end_game(
    session: Session,
    game_id: str,
    winner_id: str,
    status: str,
):
    stmt = select(Game).where(Game.id == game_id)
    game = session.exec(stmt).first()
    if game is None:
        raise Exception("Game not found")
    game.winner_id = winner_id
    game.status = status
    session.add(game)
    session.commit()
    session.refresh(game)


def get_all_games(limit: int, session: Session, offset: int):
    stmt = select(Game).limit(limit=limit).offset(offset=offset)
    games = session.exec(stmt).all()
    return games
