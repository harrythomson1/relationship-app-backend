from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserSchema(BaseModel):
    id: int
    email: str
    name: str
    created_at: datetime


class UserCreate(BaseModel):
    email: str
    name: str


class UserUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = None
