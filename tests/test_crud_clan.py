"""
Tests for app/crud/clan.py

clan.py uses sqlmodel's AsyncSession.

Functions covered:
  - create_clan
  - join_clan
  - leave_clan
  - remove_player
  - get_clan
  - get_top_clan
"""

import uuid
import pytest
import pytest_asyncio
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.crud.clan import (
    create_clan,
    join_clan,
    leave_clan,
    remove_player,
    get_clan,
    get_top_clan,
)
from app.models.clan import Clan
from app.models.players import Player


# ---------------------------------------------------------------------------
# create_clan
# ---------------------------------------------------------------------------


class TestCreateClan:
    @pytest.mark.asyncio
    async def test_create_clan_returns_clan(
        self, async_session: AsyncSession, sample_player_async: Player
    ):
        """create_clan should return a Clan instance."""
        clan = await create_clan(
            session=async_session,
            name="Dragons",
            profile_url="https://example.com/dragons.png",
            user_id=sample_player_async.id,
            description="Fierce dragons",
        )

        assert isinstance(clan, Clan)
        assert clan.name == "Dragons"
        assert clan.description == "Fierce dragons"
        assert clan.created_by == sample_player_async.id

    @pytest.mark.asyncio
    async def test_create_clan_persists_to_db(
        self, async_session: AsyncSession, sample_player_async: Player
    ):
        """create_clan should flush the clan so it is visible within the session."""
        clan = await create_clan(
            session=async_session,
            name="Knights",
            profile_url=None,
            user_id=sample_player_async.id,
            description="Noble knights",
        )

        result = await async_session.exec(select(Clan).where(Clan.name == "Knights"))
        fetched = result.first()

        assert fetched is not None
        assert fetched.id == clan.id

    @pytest.mark.asyncio
    async def test_create_clan_with_profile_url(
        self, async_session: AsyncSession, sample_player_async: Player
    ):
        """profile_url should be stored when provided."""
        url = "https://example.com/clan.png"
        clan = await create_clan(
            session=async_session,
            name="Eagles",
            profile_url=url,
            user_id=sample_player_async.id,
            description="High flyers",
        )

        assert clan.profile_url == url


# ---------------------------------------------------------------------------
# join_clan
# ---------------------------------------------------------------------------


class TestJoinClan:
    @pytest.mark.asyncio
    async def test_join_clan_associates_player(
        self,
        async_session: AsyncSession,
        sample_player_async: Player,
        sample_clan_async: Clan,
    ):
        """join_clan should set the player's clan_id and return True."""
        result = await join_clan(
            session=async_session,
            user_id=sample_player_async.id,
            clan_id=sample_clan_async.id,
        )

        assert result is True

        await async_session.refresh(sample_player_async)
        assert sample_player_async.clan_id == sample_clan_async.id

    @pytest.mark.asyncio
    async def test_join_clan_raises_when_already_in_clan(
        self,
        async_session: AsyncSession,
        sample_player_async: Player,
        sample_clan_async: Clan,
    ):
        """join_clan should raise when the player already belongs to a clan."""
        sample_player_async.clan_id = sample_clan_async.id
        async_session.add(sample_player_async)
        await async_session.commit()

        with pytest.raises(Exception, match="already in a clan"):
            await join_clan(
                session=async_session,
                user_id=sample_player_async.id,
                clan_id=sample_clan_async.id,
            )


# ---------------------------------------------------------------------------
# leave_clan
# ---------------------------------------------------------------------------


class TestLeaveClan:
    @pytest.mark.asyncio
    async def test_leave_clan_removes_association(
        self,
        async_session: AsyncSession,
        sample_player_async: Player,
        sample_clan_async: Clan,
    ):
        """leave_clan should set the player's clan_id back to None."""
        sample_player_async.clan_id = sample_clan_async.id
        async_session.add(sample_player_async)
        await async_session.commit()

        result = await leave_clan(session=async_session, user_id=sample_player_async.id)

        assert result is True

        await async_session.refresh(sample_player_async)
        assert sample_player_async.clan_id is None

    @pytest.mark.asyncio
    async def test_leave_clan_raises_when_not_in_clan(
        self,
        async_session: AsyncSession,
        sample_player_async: Player,
    ):
        """leave_clan should raise when the player has no clan."""
        assert sample_player_async.clan_id is None

        with pytest.raises(Exception, match="not part of a clan"):
            await leave_clan(session=async_session, user_id=sample_player_async.id)


# ---------------------------------------------------------------------------
# remove_player
# ---------------------------------------------------------------------------


class TestRemovePlayer:
    @pytest.mark.asyncio
    async def test_remove_player_clears_clan_id(
        self,
        async_session: AsyncSession,
        sample_player_async: Player,
        sample_clan_async: Clan,
    ):
        """remove_player should set the player's clan_id to None."""
        sample_player_async.clan_id = sample_clan_async.id
        async_session.add(sample_player_async)
        await async_session.commit()

        result = await remove_player(
            session=async_session, user_id=sample_player_async.id
        )

        assert result is True

        await async_session.refresh(sample_player_async)
        assert sample_player_async.clan_id is None


# ---------------------------------------------------------------------------
# get_clan
# ---------------------------------------------------------------------------


class TestGetClan:
    @pytest.mark.asyncio
    async def test_get_clan_returns_existing_clan(
        self,
        async_session: AsyncSession,
        sample_clan_async: Clan,
    ):
        """get_clan should return the clan matching the given id."""
        result = await get_clan(session=async_session, clan_id=sample_clan_async.id)

        clan = result.first() if hasattr(result, "first") else result
        assert clan is not None
        assert clan.id == sample_clan_async.id

    @pytest.mark.asyncio
    async def test_get_clan_returns_none_for_unknown_id(
        self,
        async_session: AsyncSession,
    ):
        """get_clan should return an empty result for an unknown id."""
        result = await get_clan(session=async_session, clan_id=str(uuid.uuid4()))

        clan = result.first() if hasattr(result, "first") else result
        assert clan is None


# ---------------------------------------------------------------------------
# get_top_clan
# ---------------------------------------------------------------------------


class TestGetTopClan:
    @pytest.mark.asyncio
    async def test_get_top_clan_returns_up_to_ten(
        self, async_session: AsyncSession, sample_player_async: Player
    ):
        """get_top_clan should return at most 10 clans ordered by ranking."""
        for i in range(1, 13):
            clan = Clan(
                name=f"Clan{i:02d}",
                ranking=i,
                description=f"Clan number {i}",
                profile_url=None,
                created_by=sample_player_async.id,
            )
            async_session.add(clan)
        await async_session.commit()

        result = await get_top_clan(session=async_session)
        clans = result.all() if hasattr(result, "all") else list(result)

        assert len(clans) == 10

    @pytest.mark.asyncio
    async def test_get_top_clan_ordered_by_ranking(
        self, async_session: AsyncSession, sample_player_async: Player
    ):
        """Clans from get_top_clan should be sorted ascending by ranking."""
        for i in [5, 2, 8, 1, 3]:
            clan = Clan(
                name=f"ClanRank{i}",
                ranking=i,
                description="ranked clan",
                profile_url=None,
                created_by=sample_player_async.id,
            )
            async_session.add(clan)
        await async_session.commit()

        result = await get_top_clan(session=async_session)
        clans = result.all() if hasattr(result, "all") else list(result)

        rankings = [c.ranking for c in clans]
        assert rankings == sorted(rankings)

    @pytest.mark.asyncio
    async def test_get_top_clan_empty_db(self, async_session: AsyncSession):
        """get_top_clan should return an empty list when no clans exist."""
        result = await get_top_clan(session=async_session)
        clans = result.all() if hasattr(result, "all") else list(result)

        assert clans == []
