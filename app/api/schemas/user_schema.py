from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class UserSchema(BaseModel):
    id: int
    email: EmailStr
    name: str
    created_at: datetime
    supabase_user_id: UUID


class UserCreate(BaseModel):
    name: str


class UserUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = None
