from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from app.api.jobs import overlap_notifier
from app.api.models import (
    DeviceToken,
    MemberRole,
    NotificationOptOut,
    Relationship,
    RelationshipMember,
    RelationshipStatus,
    User,
)
from app.api.notifications.keys import NotificationKey
from app.api.utils import push_client


async def _make_pair(db, *, a_tz, a_wake_start, a_wake_end, b_tz, b_wake_start, b_wake_end):
    a = User(
        email="a@example.com",
        name="A",
        supabase_user_id="00000000-0000-0000-0000-000000000001",
        time_zone=a_tz,
        wake_start=a_wake_start,
        wake_end=a_wake_end,
    )
    b = User(
        email="b@example.com",
        name="B",
        supabase_user_id="00000000-0000-0000-0000-000000000002",
        time_zone=b_tz,
        wake_start=b_wake_start,
        wake_end=b_wake_end,
    )
    db.add_all([a, b])
    await db.flush()

    rel = Relationship(status=RelationshipStatus.active)
    db.add(rel)
    await db.flush()

    db.add_all(
        [
            RelationshipMember(relationship_id=rel.id, user_id=a.id, role=MemberRole.partner),
            RelationshipMember(relationship_id=rel.id, user_id=b.id, role=MemberRole.partner),
            DeviceToken(user_id=a.id, token="ExponentPushToken[a]", platform="ios"),
            DeviceToken(user_id=b.id, token="ExponentPushToken[b]", platform="ios"),
        ]
    )
    await db.commit()
    return rel, a, b


@pytest.fixture
def fake_push(monkeypatch):
    calls: list[dict] = []

    async def fake_send(tokens, title, body, data=None):
        calls.append({"tokens": list(tokens), "title": title, "body": body, "data": data})
        return push_client.PushSendResult(sent=len(tokens), dead_tokens=[])

    monkeypatch.setattr(
        "app.api.services.push_notifications_service.push_client.send_push", fake_send
    )
    return calls


class TestNotifyImminentOverlaps:
    @pytest.mark.asyncio
    async def test_notifies_when_overlap_opens_in_under_10_min(
        self, db_session, fake_push, monkeypatch
    ):
        # Freeze time to 08:55 UTC. Both users wake at 09:00 local UTC ->
        # overlap opens in 5 minutes for both.
        fixed_now = datetime(2026, 1, 1, 8, 55, tzinfo=UTC)
        monkeypatch.setattr(overlap_notifier, "datetime", _FixedDatetime(fixed_now))

        rel, a, b = await _make_pair(
            db_session,
            a_tz="UTC",
            a_wake_start=9 * 60,
            a_wake_end=22 * 60,
            b_tz="UTC",
            b_wake_start=9 * 60,
            b_wake_end=22 * 60,
        )

        notified = await overlap_notifier.notify_imminent_overlaps(db_session)
        assert notified == 1
        assert len(fake_push) == 2  # one fan-out per user
        tokens_pushed = {t for call in fake_push for t in call["tokens"]}
        assert tokens_pushed == {"ExponentPushToken[a]", "ExponentPushToken[b]"}

        refreshed = (
            await db_session.execute(select(Relationship).where(Relationship.id == rel.id))
        ).scalar_one()
        assert refreshed.last_overlap_notified_at == fixed_now

    @pytest.mark.asyncio
    async def test_skips_when_overlap_opens_more_than_10_min_away(
        self, db_session, fake_push, monkeypatch
    ):
        # 06:00 UTC, both wake at 09:00 -> 180 min away. Skip.
        monkeypatch.setattr(
            overlap_notifier, "datetime", _FixedDatetime(datetime(2026, 1, 1, 6, tzinfo=UTC))
        )

        await _make_pair(
            db_session,
            a_tz="UTC",
            a_wake_start=9 * 60,
            a_wake_end=22 * 60,
            b_tz="UTC",
            b_wake_start=9 * 60,
            b_wake_end=22 * 60,
        )

        notified = await overlap_notifier.notify_imminent_overlaps(db_session)
        assert notified == 0
        assert fake_push == []

    @pytest.mark.asyncio
    async def test_does_not_notify_when_overlap_already_active(
        self, db_session, fake_push, monkeypatch
    ):
        # 13:00 UTC, both awake 09-22 -> active, not upcoming.
        monkeypatch.setattr(
            overlap_notifier, "datetime", _FixedDatetime(datetime(2026, 1, 1, 13, tzinfo=UTC))
        )

        await _make_pair(
            db_session,
            a_tz="UTC",
            a_wake_start=9 * 60,
            a_wake_end=22 * 60,
            b_tz="UTC",
            b_wake_start=9 * 60,
            b_wake_end=22 * 60,
        )

        notified = await overlap_notifier.notify_imminent_overlaps(db_session)
        assert notified == 0
        assert fake_push == []

    @pytest.mark.asyncio
    async def test_dedupes_within_window(self, db_session, fake_push, monkeypatch):
        # First call notifies; second call within dedup window does nothing.
        monkeypatch.setattr(
            overlap_notifier, "datetime", _FixedDatetime(datetime(2026, 1, 1, 8, 55, tzinfo=UTC))
        )

        await _make_pair(
            db_session,
            a_tz="UTC",
            a_wake_start=9 * 60,
            a_wake_end=22 * 60,
            b_tz="UTC",
            b_wake_start=9 * 60,
            b_wake_end=22 * 60,
        )

        assert await overlap_notifier.notify_imminent_overlaps(db_session) == 1
        fake_push.clear()
        assert await overlap_notifier.notify_imminent_overlaps(db_session) == 0
        assert fake_push == []

    @pytest.mark.asyncio
    async def test_skips_user_opted_out_but_pushes_other(self, db_session, fake_push, monkeypatch):
        monkeypatch.setattr(
            overlap_notifier, "datetime", _FixedDatetime(datetime(2026, 1, 1, 8, 55, tzinfo=UTC))
        )

        _, a, b = await _make_pair(
            db_session,
            a_tz="UTC",
            a_wake_start=9 * 60,
            a_wake_end=22 * 60,
            b_tz="UTC",
            b_wake_start=9 * 60,
            b_wake_end=22 * 60,
        )
        db_session.add(NotificationOptOut(user_id=a.id, key=NotificationKey.overlap_opening.value))
        await db_session.commit()

        notified = await overlap_notifier.notify_imminent_overlaps(db_session)
        assert notified == 1
        tokens_pushed = {t for call in fake_push for t in call["tokens"]}
        assert tokens_pushed == {"ExponentPushToken[b]"}

    @pytest.mark.asyncio
    async def test_skips_when_both_opted_out_but_still_stamps(
        self, db_session, fake_push, monkeypatch
    ):
        fixed_now = datetime(2026, 1, 1, 8, 55, tzinfo=UTC)
        monkeypatch.setattr(overlap_notifier, "datetime", _FixedDatetime(fixed_now))

        rel, a, b = await _make_pair(
            db_session,
            a_tz="UTC",
            a_wake_start=9 * 60,
            a_wake_end=22 * 60,
            b_tz="UTC",
            b_wake_start=9 * 60,
            b_wake_end=22 * 60,
        )
        db_session.add_all(
            [
                NotificationOptOut(user_id=a.id, key=NotificationKey.overlap_opening.value),
                NotificationOptOut(user_id=b.id, key=NotificationKey.overlap_opening.value),
            ]
        )
        await db_session.commit()

        notified = await overlap_notifier.notify_imminent_overlaps(db_session)
        assert notified == 0
        assert fake_push == []

        refreshed = (
            await db_session.execute(select(Relationship).where(Relationship.id == rel.id))
        ).scalar_one()
        assert refreshed.last_overlap_notified_at == fixed_now

    @pytest.mark.asyncio
    async def test_dedup_window_releases_after_23h(self, db_session, fake_push, monkeypatch):
        first = datetime(2026, 1, 1, 8, 55, tzinfo=UTC)
        monkeypatch.setattr(overlap_notifier, "datetime", _FixedDatetime(first))

        await _make_pair(
            db_session,
            a_tz="UTC",
            a_wake_start=9 * 60,
            a_wake_end=22 * 60,
            b_tz="UTC",
            b_wake_start=9 * 60,
            b_wake_end=22 * 60,
        )

        assert await overlap_notifier.notify_imminent_overlaps(db_session) == 1
        fake_push.clear()

        # 24 hours later, just before the next overlap opens.
        monkeypatch.setattr(
            overlap_notifier, "datetime", _FixedDatetime(first + timedelta(hours=24))
        )
        assert await overlap_notifier.notify_imminent_overlaps(db_session) == 1


class _FixedDatetime:
    """Stand-in for the datetime module that returns a fixed UTC `now()`."""

    def __init__(self, fixed):
        self._fixed = fixed

    def now(self, tz=None):
        return self._fixed if tz is None else self._fixed.astimezone(tz)

    def __getattr__(self, name):
        # Defer everything else (e.g. `datetime`, `timedelta`) to the real module.
        import datetime as _real

        return getattr(_real, name)
