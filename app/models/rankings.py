import uuid
from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship, Enum, Column
from typing import Optional, List


class Ranking(SQLModel, table=True):
    __tablename__ = "rankings"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    player_id: str = Field(foreign_key="players.id", index=True)

    rating: float = Field(default=1200.0, index=True)
    # rating_deviation: float = Field(default=350.0)  # Glicko RD
    # volatility: float = Field(default=0.06)

    # Performance Stats
    wins: int = Field(default=0)
    losses: int = Field(default=0)
    draws: int = Field(default=0)
    peak_rating: float = Field(default=1200.0)
    updated_at: datetime = Field(default_factory=datetime.now)
