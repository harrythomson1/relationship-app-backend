from datetime import datetime
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

MINUTES_PER_DAY = 1440


class UserSchema(BaseModel):
    id: int
    email: EmailStr
    name: str
    created_at: datetime
    supabase_user_id: UUID
    time_zone: str | None
    avatar_path: str | None
    wake_start: int = 420
    wake_end: int = 1320


class UserCreate(BaseModel):
    name: str
    time_zone: str | None = None


class PartnerSchema(BaseModel):
    id: int
    name: str
    time_zone: str
    avatar_path: str | None
    wake_start: int
    wake_end: int


class UserUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = None
    time_zone: str | None = None
    avatar_path: str | None = None
    wake_start: int | None = Field(default=None, ge=0, lt=MINUTES_PER_DAY)
    wake_end: int | None = Field(default=None, ge=0, lt=MINUTES_PER_DAY)

    @field_validator("time_zone")
    def validate_time_zone(cls, v):
        if v is not None:
            try:
                ZoneInfo(v)
            except (ZoneInfoNotFoundError, KeyError) as e:
                raise ValueError("Timezone is invalid") from e
        return v
