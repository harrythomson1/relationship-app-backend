import logging

from app.api.models import Relationship, RelationshipMember
from app.api.notifications.keys import NotificationKey
from app.api.repositories.relationship_repository import (
    DuplicateEntryError,
    RelationshipMemberNotFoundError,
    RelationshipNotFoundError,
)

logger = logging.getLogger(__name__)


class InvalidInviteUserError(Exception):
    pass


class RelationshipsService:
    def __init__(self, relationship_repository, db, user_repository):
        self.relationship_repository = relationship_repository
        self.user_repository = user_repository
        self.db = db

    async def add(self, current_user, relationship_info, user_service, relationship_invite_service):
        invite = await relationship_invite_service.get_by_token(relationship_info.invite_token)
        partner = await user_service.get_by_email(invite.inviter_email)
        try:
            await self.relationship_repository.get_existing_relationship_between_users(
                current_user.id, partner.id
            )
            raise DuplicateEntryError("A relationship between these users already exists")
        except (RelationshipNotFoundError, RelationshipMemberNotFoundError):
            pass
        if current_user.email != invite.invitee_email:
            raise InvalidInviteUserError("Current user does not match user from the invite")
        async with self.db.begin_nested():
            if current_user.id == partner.id:
                raise ValueError("A relationship must have two distinct users")
            rel = Relationship(type=relationship_info.type, status=relationship_info.status)
            rel = await self.relationship_repository.add_relationship(rel)
            rel_member_1 = RelationshipMember(
                relationship_id=rel.id, user_id=current_user.id, role=relationship_info.role
            )
            rel_member_2 = RelationshipMember(
                relationship_id=rel.id, user_id=partner.id, role=relationship_info.role
            )
            await self.relationship_repository.add_relationship_members(rel_member_1)
            await self.relationship_repository.add_relationship_members(rel_member_2)
            await relationship_invite_service.mark_accepted(invite, rel.id)
        await self.db.commit()
        return rel

    async def get_partner_time_zone(self, current_user):
        partner_member = await self.relationship_repository.get_partner(current_user)
        partner = await self.user_repository.get_by_id(partner_member.user_id)
        return {"time_zone": partner.time_zone, "name": partner.name}

    async def get_partner(self, current_user):
        partner_member = await self.relationship_repository.get_partner(current_user)
        partner = await self.user_repository.get_by_id(partner_member.user_id)
        return partner

    async def get_by_id(self, realtionship_id, user_id):
        rel = await self.relationship_repository.get_by_id(realtionship_id, user_id)
        return rel

    async def get_by_user_id(self, user_id):
        return await self.relationship_repository.get_by_user_id(user_id)

    async def update(
        self,
        current_user,
        update_data,
        push_service=None,
        notification_preferences_repository=None,
    ):
        existing = await self.relationship_repository.get_by_user_id(current_user.id)
        old_next_meet_at = existing.next_meet_at
        updated = await self.relationship_repository.update(current_user.id, update_data)

        next_meet_at_changed = (
            "next_meet_at" in update_data.model_dump(exclude_unset=True)
            and updated.next_meet_at != old_next_meet_at
        )
        if next_meet_at_changed and push_service is not None:
            await self._notify_partner_of_countdown_update(
                current_user, updated, push_service, notification_preferences_repository
            )
        return updated

    async def _notify_partner_of_countdown_update(
        self, current_user, relationship, push_service, prefs_repo
    ):
        try:
            partner = await self.get_partner(current_user)
        except RelationshipMemberNotFoundError:
            return
        if prefs_repo is not None:
            opt_outs = await prefs_repo.list_opt_outs(partner.id)
            if NotificationKey.countdown_updated.value in opt_outs:
                return

        if relationship.next_meet_at is None:
            title = "Countdown cleared"
            body = f"{current_user.name} removed the countdown"
        else:
            title = "Countdown updated"
            body = f"{current_user.name} set a new date"

        try:
            await push_service.send_to_user(
                user_id=partner.id,
                title=title,
                body=body,
                data={
                    "type": NotificationKey.countdown_updated.value,
                    "relationship_id": relationship.id,
                },
            )
        except Exception:
            logger.exception("Failed to send countdown-updated push to user %s", partner.id)

    async def delete(self, user_id, relationship_invite_service=None):
        relationship = await self.relationship_repository.get_by_user_id(user_id)
        if relationship_invite_service is not None:
            await relationship_invite_service.mark_relationship_ended(relationship.id)
        return await self.relationship_repository.delete(user_id)
