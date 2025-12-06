import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr

from app.api.models import InviteStatus, MemberRole


class RelationshipInviteSchema(BaseModel):
    id: int
    token: uuid.UUID
    relaitionship_id: int | None = None
    inviter_user_id: int | None = None
    inviter_email: EmailStr
    invitee_user_id: int | None = None
    invitee_email: EmailStr
    role: MemberRole
    status: InviteStatus
    expires_at: datetime | None = None
    accepted_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class RelationshipInviteCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: MemberRole = MemberRole.partner
    invitee_email: EmailStr
