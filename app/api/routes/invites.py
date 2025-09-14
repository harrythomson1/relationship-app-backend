from fastapi import APIRouter, Depends, HTTPException, status

from app.api.auth.utils import get_current_user
from app.api.dependencies import get_relationship_invites_service
from app.api.repositories.relationship_invite_repository import DuplicateInviteError
from app.api.schemas.relationship_invite_schema import (
    RelationshipInviteCreate,
    RelationshipInviteSchema,
)
from app.api.services.relationship_invites_service import RelationshipInvitesService

router = APIRouter(prefix="/relationships", tags=["relationships"])

relationship_invite_service_dependency = Depends(get_relationship_invites_service)
get_current_user_dependency = Depends(get_current_user)


@router.post(
    "/invites", status_code=status.HTTP_201_CREATED, response_model=RelationshipInviteSchema
)
async def add_relationship_invite(
    relationship_invite_info: RelationshipInviteCreate,
    service: RelationshipInvitesService = relationship_invite_service_dependency,
    current_user=get_current_user_dependency,
):
    try:
        relationship_invite = await service.add(relationship_invite_info, current_user.id)
        return relationship_invite
    except DuplicateInviteError as e:
        raise HTTPException(status_code=409, detail={"message": str(e)}) from e
