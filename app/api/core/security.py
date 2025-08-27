import os
from datetime import datetime, timedelta

from dotenv import load_dotenv
from jose import jwt

load_dotenv()

ALGORITHM = "HS256"

_secret = os.getenv("JWT_SECRET")
if _secret is None:
    raise ValueError("JWT_SECRET not set in environment")
SECRET_KEY: str = _secret


def create_access_token(payload: dict, expires_minutes: int = 30):
    to_encode = payload.copy()
    now = datetime.now()
    expire = now + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire, "iat": now, "sub": str(payload.get("sub"))})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
