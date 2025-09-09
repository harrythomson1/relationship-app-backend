from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field

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
    user_ids: Annotated[list[int], Field(min_length=2, max_length=2)]
    role: MemberRole = MemberRole.partner
