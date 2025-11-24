from collections.abc import Mapping
from typing import Any
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError

from app.api.core.database_connection import get_db
from app.api.core.security import verify_access_token
from app.api.repositories.user_repository import UserNotFoundError, UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users")
database_dependency = Depends(get_db)


async def get_current_claims(
    token: str = Depends(oauth2_scheme),
) -> Mapping[str, Any]:
    try:
        payload: Mapping[str, Any] = verify_access_token(token)
        if payload.get("sub") is None:
            raise HTTPException(status_code=401, detail="Invalid token: missing subject")
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        ) from e


async def get_current_user(
    claims: Mapping[str, Any] = Depends(get_current_claims),
    db=database_dependency,
):
    sub = claims.get("sub")
    try:
        supabase_user_id = UUID(str(sub))
    except (TypeError, ValueError) as e:
        raise HTTPException(status_code=401, detail="Invalid token subject") from e

    repo = UserRepository(db)
    try:
        user = await repo.get_by_supabase_user_id(supabase_user_id)
        return user
    except UserNotFoundError as e:
        raise UserNotFoundError("User not found") from e
