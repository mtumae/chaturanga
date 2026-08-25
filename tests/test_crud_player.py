"""
Tests for app/crud/player.py

player.py uses a synchronous sqlmodel Session.

Functions covered:
  - create_player
  - update_activity
"""

import pytest
from sqlmodel import select, Session

from app.crud.player import create_player, update_activity
from app.models.players import Player
from app.models.rankings import Ranking


# ---------------------------------------------------------------------------
# create_player
# ---------------------------------------------------------------------------


class TestCreatePlayer:
    @pytest.mark.asyncio
    async def test_create_player_persists_player(self, sync_session: Session):
        """A new Player row should be committed to the database."""
        await create_player(
            session=sync_session,
            id="user_abc",
            username="alice",
            email="alice@example.com",
            avatar_url="https://example.com/alice.png",
        )

        result = sync_session.exec(select(Player).where(Player.id == "user_abc"))
        player = result.first()

        assert player is not None
        assert player.id == "user_abc"
        assert player.username == "alice"
        assert player.email == "alice@example.com"
        assert player.avatar_url == "https://example.com/alice.png"

    @pytest.mark.asyncio
    async def test_create_player_sets_is_active_true(self, sync_session: Session):
        """Newly created players should be marked active."""
        await create_player(
            session=sync_session,
            id="user_active",
            username="bobactive",
            email="bob@example.com",
            avatar_url=None,
        )

        result = sync_session.exec(
            select(Player).where(Player.id == "user_active")
        )
        player = result.first()

        assert player is not None
        assert player.is_active is True

    @pytest.mark.asyncio
    async def test_create_player_creates_ranking(self, sync_session: Session):
        """A Ranking row should be created alongside the Player."""
        await create_player(
            session=sync_session,
            id="user_rank",
            username="rankplayer",
            email="rank@example.com",
            avatar_url=None,
        )

        result = sync_session.exec(
            select(Ranking).where(Ranking.player_id == "user_rank")
        )
        ranking = result.first()

        assert ranking is not None
        assert ranking.rating == 1200.0
        assert ranking.wins == 0
        assert ranking.losses == 0
        assert ranking.draws == 0

    @pytest.mark.asyncio
    async def test_create_player_clan_id_is_none(self, sync_session: Session):
        """A new player should not be associated with any clan."""
        await create_player(
            session=sync_session,
            id="user_noclan",
            username="noclanplayer",
            email="noclan@example.com",
            avatar_url=None,
        )

        result = sync_session.exec(
            select(Player).where(Player.id == "user_noclan")
        )
        player = result.first()

        assert player is not None
        assert player.clan_id is None


# ---------------------------------------------------------------------------
# update_activity
# ---------------------------------------------------------------------------


class TestUpdateActivity:
    @pytest.mark.asyncio
    async def test_update_activity_sets_is_active(
        self, sync_session: Session, sample_player_sync: Player
    ):
        """update_activity should flip is_active to True."""
        # Start with an inactive player.
        sample_player_sync.is_active = False
        sync_session.add(sample_player_sync)
        sync_session.commit()

        await update_activity(session=sync_session, id=sample_player_sync.id)

        result = sync_session.exec(
            select(Player).where(Player.id == sample_player_sync.id)
        )
        player = result.first()

        assert player is not None
        assert player.is_active is True

    @pytest.mark.asyncio
    async def test_update_activity_nonexistent_player_raises(
        self, sync_session: Session
    ):
        """update_activity should raise an Exception for an unknown player id."""
        with pytest.raises(Exception, match="Player does not exist"):
            await update_activity(session=sync_session, id="user_ghost")
