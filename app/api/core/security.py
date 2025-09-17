import os
from datetime import datetime, timedelta

import requests
from dotenv import load_dotenv
from fastapi import HTTPException, status
from jose import JWTError, jwt

load_dotenv()

JWKS_URL = "https://kzuztavhripyncgxtzhr.supabase.co/auth/v1/.well-known/jwks.json"
ALGORITHM = "ES256"
PROJECT_URL = "https://kzuztavhripyncgxtzhr.supabase.co/auth/v1"
AUDIENCE = "authenticated"

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
        response = requests.get(JWKS_URL)
        response.raise_for_status()

        jwks = response.json()
        header = jwt.get_unverified_header(token)
        alg = header.get("alg")
        header_kid = header.get("kid")
        if alg != ALGORITHM:
            raise HTTPException(status_code=401, detail="Unexpected alg")
        try:
            key = next(key for key in jwks["keys"] if key["kid"] == header_kid)
        except StopIteration as e:
            raise HTTPException(status_code=401, detail="Unknown key id (kid)") from e
        payload = jwt.decode(
            token,
            key=key,
            algorithms=[ALGORITHM],
            issuer=PROJECT_URL,
            audience=AUDIENCE,
            options={"leeway": 60},
        )
        sub: str | None = payload.get("sub")
        if sub is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is missing subject claim"
            )
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is invalid or expired"
        ) from e
