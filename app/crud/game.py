import uuid
from typing import Optional, List
from fastapi.exceptions import HTTPException

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import Field, SQLModel, Relationship, Enum, Column, Session
from app.models.game import Game
from app.models.players import Player
from datetime import datetime


class GameStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


async def create_game(
    session:Session,
    player_id:uuid.UUID,
):
    game = Game(
        fen=None,
        moves_history=[],
        pgn=None,
        created_by=player_id,
        winner_id=None,
        termination_reason=None
    )

    session.add(game)
    session.flush()
    session.commit()

async def save_game(
    session:Session,
    game_id:uuid.UUID,
    player_id:uuid.UUID,
    fen:str,
    moves_history:List[str],
    pgn:str,
    updated_at:datetime,
    winner_id:Optional[uuid.UUID],
    status:str
):
    stmt = select(Game).where(Game.id==game_id)
    game = session.exec(stmt).first()
    if game is None:
        raise Exception("Game not found")

    if game.created_by != player_id:
        raise Exception("Player is attempted to save a game they did not create.")
    game.fen=fen
    game.moves_history = moves_history
    game.pgn = pgn
    game.winner_id = winner_id
    game.status = status

    session.add(game)
    session.commit()
    session.refresh(game)


async def end_game(
    session:Session,
    game_id:uuid.UUID,
    winner_id:str,
    status:str,
):
    stmt = select(Game).where(Game.id==game_id)
    game = session.exec(stmt).first()
    if game is None:
        raise Exception("Game not found")
    game.winner_id = winner_id
    game.status = status
    session.add(game)
    session.commit()
    session.refresh(game)
