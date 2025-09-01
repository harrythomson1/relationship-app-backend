from pydantic import BaseModel, EmailStr

from app.api.schemas.user_schema import UserSchema


class DevLoginRequest(BaseModel):
    email: EmailStr


class AuthResponse(BaseModel):
    user: UserSchema
    token: str
