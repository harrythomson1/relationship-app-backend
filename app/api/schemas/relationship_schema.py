from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.api.models import MemberRole, RelationshipStatus, RelationshipType


class RelationshipSchema(BaseModel):
    id: int
    type: RelationshipType
    status: RelationshipStatus
    created_at: datetime
    updated_at: datetime
    next_meet_at: datetime | None = None


class RelationshipCreate(BaseModel):
    type: RelationshipType = RelationshipType.romantic
    status: RelationshipStatus = RelationshipStatus.active
    invite_token: str
    role: MemberRole = MemberRole.partner


class RelationshipUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: RelationshipType | None = None
    status: RelationshipStatus | None = None
    next_meet_at: datetime | None = None
