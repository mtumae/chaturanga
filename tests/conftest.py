"""
Shared fixtures for CRUD tests.

Uses an in-memory SQLite database so no external services are needed.
Each test function gets a fresh database.

- `async_session` — for CRUD functions that use AsyncSession  (clan.py)
- `sync_session`  — for CRUD functions that use the sync Session (game.py, player.py)
"""

import pytest
import pytest_asyncio
from sqlmodel import SQLModel, Session, create_engine
from sqlmodel.pool import StaticPool
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

# Import all models so SQLModel registers their metadata before table creation.
from app.models.players import Player   # noqa: F401
from app.models.clan import Clan        # noqa: F401
from app.models.game import Game        # noqa: F401
from app.models.rankings import Ranking # noqa: F401


# ---------------------------------------------------------------------------
# Async session (used by clan.py)
# ---------------------------------------------------------------------------

ASYNC_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="function")
async def async_session() -> AsyncSession:
    """Yield a fresh AsyncSession backed by an in-memory SQLite database."""
    engine = create_async_engine(
        ASYNC_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with AsyncSession(engine, expire_on_commit=False) as sess:
        yield sess

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)

    await engine.dispose()


# ---------------------------------------------------------------------------
# Sync session (used by game.py and player.py)
# ---------------------------------------------------------------------------

SYNC_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def sync_session() -> Session:
    """Yield a fresh sync Session backed by an in-memory SQLite database."""
    engine = create_engine(
        SYNC_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session

    SQLModel.metadata.drop_all(engine)
    engine.dispose()


# ---------------------------------------------------------------------------
# Convenience factory fixtures — sync variants
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_player_sync(sync_session: Session) -> Player:
    """Insert and return a minimal Player row using the sync session."""
    player = Player(
        id="user_test123",
        username="testplayer",
        email="test@example.com",
        avatar_url="https://example.com/avatar.png",
        is_active=True,
        clan_id=None,
    )
    sync_session.add(player)
    sync_session.commit()
    sync_session.refresh(player)
    return player


@pytest.fixture
def sample_clan_sync(sync_session: Session, sample_player_sync: Player) -> Clan:
    """Insert and return a minimal Clan row using the sync session."""
    clan = Clan(
        name="TestClan",
        ranking=1,
        description="A test clan",
        profile_url=None,
        created_by=sample_player_sync.id,
    )
    sync_session.add(clan)
    sync_session.commit()
    sync_session.refresh(clan)
    return clan


# ---------------------------------------------------------------------------
# Convenience factory fixtures — async variants
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def sample_player_async(async_session: AsyncSession) -> Player:
    """Insert and return a minimal Player row using the async session."""
    player = Player(
        id="user_test123",
        username="testplayer",
        email="test@example.com",
        avatar_url="https://example.com/avatar.png",
        is_active=True,
        clan_id=None,
    )
    async_session.add(player)
    await async_session.commit()
    await async_session.refresh(player)
    return player


@pytest_asyncio.fixture
async def sample_clan_async(
    async_session: AsyncSession, sample_player_async: Player
) -> Clan:
    """Insert and return a minimal Clan row using the async session."""
    clan = Clan(
        name="TestClan",
        ranking=1,
        description="A test clan",
        profile_url=None,
        created_by=sample_player_async.id,
    )
    async_session.add(clan)
    await async_session.commit()
    await async_session.refresh(clan)
    return clan
