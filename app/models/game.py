import uuid
from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship, Enum, Column, JSON
from typing import Optional, List


class Game(SQLModel, table=True):
    __tablename__ = "games"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    status: str = Field(default="pending", index=True)

    # Clock configuration
    # initial_time_seconds: int = Field(default=600)  # e.g., 600 for 10 min
    # increment_seconds: int = Field(default=0)

    # Board state snapshots
    fen: Optional[str] = Field(default=None)  # Final/Current FEN for Chess
    moves_history: List[str] = Field(default=[], sa_column=Column(JSON))  # Ordered UCI
    pgn: Optional[str] = Field(default=None)  # Full PGN notation (Chess)
    created_by: str = Field(foreign_key="players.id", index=True)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    ended_at: Optional[datetime] = Field(default=None)

    # Outcome summary
    winner_id: Optional[str] = Field(default=None, foreign_key="players.id")
    termination_reason: Optional[str] = Field(
        default=None
    )  # "checkmate", "timeout", "resignation", "bingo"
