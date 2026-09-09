"""
Tests for app/crud/game.py

game.py uses a synchronous sqlmodel Session.

Functions covered:
  - create_game
  - save_game
  - end_game
"""

import uuid
import pytest
import pytest_asyncio
from sqlmodel import select, Session

from app.crud.game import create_game, save_game, end_game, GameStatus
from app.models.game import Game
from app.models.players import Player


# ---------------------------------------------------------------------------
# create_game
# ---------------------------------------------------------------------------


class TestCreateGame:
    @pytest.mark.asyncio
    async def test_create_game_persists_game(
        self, sync_session: Session, sample_player_sync: Player
    ):
        """create_game should commit a new Game row to the database."""
        await create_game(session=sync_session, player_id=sample_player_sync.id)

        result = sync_session.exec(
            select(Game).where(Game.created_by == sample_player_sync.id)
        )
        game = result.first()

        assert game is not None
        assert game.created_by == sample_player_sync.id

    @pytest.mark.asyncio
    async def test_create_game_default_status_is_pending(
        self, sync_session: Session, sample_player_sync: Player
    ):
        """A newly created game should have PENDING status."""
        await create_game(session=sync_session, player_id=sample_player_sync.id)

        result = sync_session.exec(
            select(Game).where(Game.created_by == sample_player_sync.id)
        )
        game = result.first()

        assert game is not None
        assert game.status == GameStatus.PENDING

    @pytest.mark.asyncio
    async def test_create_game_initial_fields_are_none(
        self, sync_session: Session, sample_player_sync: Player
    ):
        """fen, pgn, winner_id, and termination_reason should be None initially."""
        await create_game(session=sync_session, player_id=sample_player_sync.id)

        result = sync_session.exec(
            select(Game).where(Game.created_by == sample_player_sync.id)
        )
        game = result.first()

        assert game is not None
        assert game.fen is None
        assert game.pgn is None
        assert game.winner_id is None
        assert game.termination_reason is None

    @pytest.mark.asyncio
    async def test_create_game_moves_history_is_empty(
        self, sync_session: Session, sample_player_sync: Player
    ):
        """moves_history should start as an empty list."""
        await create_game(session=sync_session, player_id=sample_player_sync.id)

        result = sync_session.exec(
            select(Game).where(Game.created_by == sample_player_sync.id)
        )
        game = result.first()

        assert game is not None
        assert game.moves_history == []


# ---------------------------------------------------------------------------
# Shared helper to create and retrieve a persisted game
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def persisted_game(sync_session: Session, sample_player_sync: Player) -> Game:
    """Create and return a Game that is already committed to the DB."""
    await create_game(session=sync_session, player_id=sample_player_sync.id)
    result = sync_session.exec(
        select(Game).where(Game.created_by == sample_player_sync.id)
    )
    return result.first()


# ---------------------------------------------------------------------------
# save_game
# ---------------------------------------------------------------------------


class TestSaveGame:
    @pytest.mark.asyncio
    async def test_save_game_updates_fen(
        self,
        sync_session: Session,
        sample_player_sync: Player,
        persisted_game: Game,
    ):
        """save_game should update the fen field."""
        new_fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"

        await save_game(
            session=sync_session,
            game_id=persisted_game.id,
            player_id=sample_player_sync.id,
            fen=new_fen,
            moves_history=["e2e4"],
            pgn="1. e4",
            updated_at=None,
            winner_id=None,
            status=GameStatus.IN_PROGRESS,
        )

        result = sync_session.exec(select(Game).where(Game.id == persisted_game.id))
        game = result.first()

        assert game is not None
        assert game.fen == new_fen

    @pytest.mark.asyncio
    async def test_save_game_updates_moves_history(
        self,
        sync_session: Session,
        sample_player_sync: Player,
        persisted_game: Game,
    ):
        """save_game should persist the moves_history list."""
        moves = ["e2e4", "e7e5", "g1f3"]

        await save_game(
            session=sync_session,
            game_id=persisted_game.id,
            player_id=sample_player_sync.id,
            fen="some_fen",
            moves_history=moves,
            pgn="1. e4 e5 2. Nf3",
            updated_at=None,
            winner_id=None,
            status=GameStatus.IN_PROGRESS,
        )

        result = sync_session.exec(select(Game).where(Game.id == persisted_game.id))
        game = result.first()

        assert game is not None
        assert game.moves_history == moves

    @pytest.mark.asyncio
    async def test_save_game_updates_status(
        self,
        sync_session: Session,
        sample_player_sync: Player,
        persisted_game: Game,
    ):
        """save_game should update the game status."""
        await save_game(
            session=sync_session,
            game_id=persisted_game.id,
            player_id=sample_player_sync.id,
            fen="final_fen",
            moves_history=[],
            pgn="",
            updated_at=None,
            winner_id=sample_player_sync.id,
            status=GameStatus.COMPLETED,
        )

        result = sync_session.exec(select(Game).where(Game.id == persisted_game.id))
        game = result.first()

        assert game is not None
        assert game.status == GameStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_save_game_raises_for_missing_game(
        self, sync_session: Session, sample_player_sync: Player
    ):
        """save_game should raise an Exception when the game_id does not exist."""
        with pytest.raises(Exception, match="Game not found"):
            await save_game(
                session=sync_session,
                game_id=str(uuid.uuid4()),
                player_id=sample_player_sync.id,
                fen="fen",
                moves_history=[],
                pgn="",
                updated_at=None,
                winner_id=None,
                status=GameStatus.IN_PROGRESS,
            )

    @pytest.mark.asyncio
    async def test_save_game_raises_for_wrong_player(
        self,
        sync_session: Session,
        sample_player_sync: Player,
        persisted_game: Game,
    ):
        """save_game should raise when the caller is not the game creator."""
        other_player = Player(
            id="user_other",
            username="otherplayer",
            email="other@example.com",
            avatar_url=None,
            is_active=True,
            clan_id=None,
        )
        sync_session.add(other_player)
        sync_session.commit()

        with pytest.raises(Exception, match="did not create"):
            await save_game(
                session=sync_session,
                game_id=persisted_game.id,
                player_id=other_player.id,
                fen="fen",
                moves_history=[],
                pgn="",
                updated_at=None,
                winner_id=None,
                status=GameStatus.IN_PROGRESS,
            )


# ---------------------------------------------------------------------------
# end_game
# ---------------------------------------------------------------------------


class TestEndGame:
    @pytest.mark.asyncio
    async def test_end_game_sets_winner_and_status(
        self,
        sync_session: Session,
        sample_player_sync: Player,
        persisted_game: Game,
    ):
        """end_game should update the winner_id and status."""
        await end_game(
            session=sync_session,
            game_id=persisted_game.id,
            winner_id=sample_player_sync.id,
            status=GameStatus.COMPLETED,
        )

        result = sync_session.exec(select(Game).where(Game.id == persisted_game.id))
        game = result.first()

        assert game is not None
        assert game.winner_id == sample_player_sync.id
        assert game.status == GameStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_end_game_raises_for_missing_game(
        self, sync_session: Session, sample_player_sync: Player
    ):
        """end_game should raise an Exception when the game_id does not exist."""
        with pytest.raises(Exception, match="Game not found"):
            await end_game(
                session=sync_session,
                game_id=str(uuid.uuid4()),
                winner_id=sample_player_sync.id,
                status=GameStatus.COMPLETED,
            )
