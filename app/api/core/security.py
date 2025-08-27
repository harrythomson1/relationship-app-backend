import os
from datetime import datetime, timedelta

from dotenv import load_dotenv
from fastapi import HTTPException, status
from jose import JWTError, jwt

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


def verify_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is missing subject claim"
            )
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is invalid or expired"
        ) from e
