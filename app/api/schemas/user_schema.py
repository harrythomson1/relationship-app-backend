from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class UserSchema(BaseModel):
    id: int
    email: EmailStr
    name: str
    created_at: datetime


class UserCreate(BaseModel):
    email: EmailStr
    name: str


class UserUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = None
