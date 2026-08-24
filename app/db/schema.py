import uuid
from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship, Enum, Column
from pydantic import Optional, List





class Ranking(SQLModel, table=True):
    __tablename__ = "rankings"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    player_id: uuid.UUID = Field(foreign_key="players.id", index=True)

    # Glicko-2 / Elo metrics
    rating: float = Field(default=1200.0, index=True)
    rating_deviation: float = Field(default=350.0)  # Glicko RD
    volatility: float = Field(default=0.06)

    # Performance Stats
    wins: int = Field(default=0)
    losses: int = Field(default=0)
    draws: int = Field(default=0)
    peak_rating: float = Field(default=1200.0)
    updated_at: datetime = Field(default_factory=datetime.now().isoformat)

    # Relationships
    player: Player = Relationship(back_populates="rankings")



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
    is_bot: bool = Field(default=False)
    created_at: datetime =  Field(default_factory=datetime.now().isoformat)
    last_online: Optional[datetime] = Field(default=None)

    # Clan Association
    clan_id: Optional[uuid.UUID] = Field(default=None, foreign_key="clans.id")

    # Relationships
    rankings: List["Ranking"] = Relationship(back_populates="player")


class GameStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"

class Game(SQLModel, table=True):
    __tablename__ = "games"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    # game_type: GameType = Field(index=True, default='chess')

    status: GameStatus = Field(default=GameStatus.PENDING, index=True)

    # Clock configuration
    initial_time_seconds: int = Field(default=600)  # e.g., 600 for 10 min
    increment_seconds: int = Field(default=0)

    # Board state snapshots
    fen: Optional[str] = Field(default=None)  # Final/Current FEN for Chess
    moves_history: List[str] = Field(default=[], sa_column=Column(JSON))  # Ordered UCI
    pgn: Optional[str] = Field(default=None)  # Full PGN notation (Chess)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now().isoformat)
    started_at: Optional[datetime] = Field(default=None)
    ended_at: Optional[datetime] = Field(default=None)

    # Outcome summary
    winner_id: Optional[uuid.UUID] = Field(default=None, foreign_key="players.id")
    termination_reason: Optional[str] = Field(default=None)  # "checkmate", "timeout", "resignation", "bingo"
