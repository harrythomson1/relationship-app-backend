import uuid
from datetime import datetime

from pydantic import BaseModel

from app.api.models import InviteStatus, MemberRole


class RelationshipInviteSchema(BaseModel):
    id: int
    token: uuid.UUID
    relaitionship_id: int | None = None
    inviter_user_id: int | None = None
    invitee_user_id: int | None = None
    invitee_email: str
    role: MemberRole
    status: InviteStatus
    expires_at: datetime | None = None
    accepted_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
