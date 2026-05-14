"""Scan active relationships, send a push when an overlap window is about
to open. Dedupes by Relationship.last_overlap_notified_at — once we've
notified for a given relationship, we won't send again until the dedup
window has elapsed.
"""

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.api.jobs.overlap_calc import UserSchedule, calculate_overlap
from app.api.models import Relationship, RelationshipMember, RelationshipStatus, User
from app.api.repositories.device_token_repository import DeviceTokenRepository
from app.api.services.push_notifications_service import PushNotificationsService

logger = logging.getLogger(__name__)

NOTIFY_WHEN_MINUTES_UNTIL_OPEN_LE = 10
DEDUP_WINDOW = timedelta(hours=23)


async def notify_imminent_overlaps(db) -> int:
    """Send overlap-opening pushes for relationships whose overlap opens soon.

    Returns the number of relationships that were notified.
    """
    now = datetime.now(UTC)
    eligible_cutoff = now - DEDUP_WINDOW

    relationships = (
        (
            await db.execute(
                select(Relationship).where(
                    Relationship.status == RelationshipStatus.active,
                    (Relationship.last_overlap_notified_at.is_(None))
                    | (Relationship.last_overlap_notified_at <= eligible_cutoff),
                )
            )
        )
        .scalars()
        .all()
    )

    push_service = PushNotificationsService(DeviceTokenRepository(db))

    notified = 0
    for rel in relationships:
        members = (
            (
                await db.execute(
                    select(RelationshipMember).where(RelationshipMember.relationship_id == rel.id)
                )
            )
            .scalars()
            .all()
        )
        if len(members) != 2:
            continue

        users = (
            (await db.execute(select(User).where(User.id.in_([m.user_id for m in members]))))
            .scalars()
            .all()
        )
        if len(users) != 2 or any(u.time_zone is None for u in users):
            continue

        a, b = users
        status = calculate_overlap(
            now,
            UserSchedule(time_zone=a.time_zone, wake_start=a.wake_start, wake_end=a.wake_end),
            UserSchedule(time_zone=b.time_zone, wake_start=b.wake_start, wake_end=b.wake_end),
        )

        if status.state != "upcoming":
            continue
        if (status.minutes_until_open or 0) > NOTIFY_WHEN_MINUTES_UNTIL_OPEN_LE:
            continue

        for u in users:
            partner = b if u.id == a.id else a
            try:
                await push_service.send_to_user(
                    user_id=u.id,
                    title="Your window is opening",
                    body=f"You and {partner.name} can chat in a few minutes 🧡",
                    data={"type": "overlap_opening", "partner_user_id": partner.id},
                )
            except Exception:
                logger.exception("Failed to send overlap push to user %s", u.id)

        rel.last_overlap_notified_at = now
        await db.commit()
        notified += 1

    return notified
