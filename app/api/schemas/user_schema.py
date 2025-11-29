from datetime import datetime
from uuid import UUID
from zoneinfo import available_timezones

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator


class UserSchema(BaseModel):
    id: int
    email: EmailStr
    name: str
    created_at: datetime
    supabase_user_id: UUID
    time_zone: str | None


class UserCreate(BaseModel):
    name: str
    time_zone: str | None = None


class UserUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = None
    time_zone: str | None = None

    @field_validator("time_zone")
    def validate_time_zone(cls, v):
        if v is not None and v not in available_timezones():
            raise ValueError("Timezone is invalid")
        return v
