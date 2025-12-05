import time

import requests
from fastapi import HTTPException, status
from jose import JWTError, jwt

JWKS_URL = "https://lkfhoxaagckacfjpnkqw.supabase.co/auth/v1/.well-known/jwks.json"
ALGORITHM = "ES256"
PROJECT_URL = "https://lkfhoxaagckacfjpnkqw.supabase.co/auth/v1"
AUDIENCE = "authenticated"

_JWKS_CACHE = None
_JWKS_CACHE_TIME = 0
_JWKS_TTL = 300  # 5 minutes


def fetch_jwks_with_retry():
    global _JWKS_CACHE, _JWKS_CACHE_TIME
    if _JWKS_CACHE and (time.time() - _JWKS_CACHE_TIME) < _JWKS_TTL:
        return _JWKS_CACHE

    attempts = 3
    delay = 0.1
    last_exception = None

    for _ in range(attempts):
        try:
            response = requests.get(JWKS_URL, timeout=2)
            response.raise_for_status()
            data = response.json()
            _JWKS_CACHE = data
            _JWKS_CACHE_TIME = time.time()
            return data
        except Exception as e:
            last_exception = e
            time.sleep(delay)
            delay *= 2

    if _JWKS_CACHE:
        return _JWKS_CACHE

    raise HTTPException(
        status_code=503, detail="Unable to fetch JWKS keys from Supabase"
    ) from last_exception


def verify_access_token(token: str):
    try:
        jwks = fetch_jwks_with_retry()
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
