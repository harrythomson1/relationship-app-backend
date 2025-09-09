from datetime import datetime

from pydantic import BaseModel

from app.api.models import RelationshipStatus, RelationshipType


class RelationshipSchema(BaseModel):
    id: int
    type: RelationshipType
    status: RelationshipStatus
    created_at: datetime
    updated_at: datetime


class RelationshipCreate(BaseModel):
    type: RelationshipType = RelationshipType.romantic
    status: RelationshipStatus = RelationshipStatus.pending
