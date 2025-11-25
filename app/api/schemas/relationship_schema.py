from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr

from app.api.models import MemberRole, RelationshipStatus, RelationshipType


class RelationshipSchema(BaseModel):
    id: int
    type: RelationshipType
    status: RelationshipStatus
    created_at: datetime
    updated_at: datetime


class RelationshipCreate(BaseModel):
    type: RelationshipType = RelationshipType.romantic
    status: RelationshipStatus = RelationshipStatus.pending
    partner_email: EmailStr
    role: MemberRole = MemberRole.partner


class RelationshipUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: RelationshipType
    status: RelationshipStatus
