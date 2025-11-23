import requests
from fastapi import HTTPException, status
from jose import JWTError, jwt

JWKS_URL = "https://lkfhoxaagckacfjpnkqw.supabase.co/auth/v1/.well-known/jwks.json"
ALGORITHM = "ES256"
PROJECT_URL = "https://lkfhoxaagckacfjpnkqw.supabase.co/auth/v1"
AUDIENCE = "authenticated"


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
