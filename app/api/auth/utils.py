from collections.abc import Mapping
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError

from app.api.core.database_connection import get_db
from app.api.core.security import verify_access_token
from app.api.repositories.user_repository import UserNotFoundError, UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/dev-login")
database_dependency = Depends(get_db)


async def get_current_claims(token: str = Depends(oauth2_scheme)):
    try:
        payload: Mapping[str, Any] = verify_access_token(token)
        if payload.get("sub") is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return payload

    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        ) from e


async def get_current_user(
    payload,
    db=database_dependency,
):
    try:
        sub = payload.get("sub")
        try:
            user_id = str(sub)
        except (TypeError, ValueError) as e:
            raise HTTPException(status_code=401, detail="Invalid token subject") from e

        repo = UserRepository(db)
        user = await repo.get_by_supabase_user_id(user_id)
        return user

    except (JWTError, UserNotFoundError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        ) from e
