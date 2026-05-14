from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.api.auth.utils import get_current_user
from app.api.dependencies import (
    get_relationship_invites_service,
    get_relationships_service,
    get_users_service,
)
from app.api.repositories.relationship_invite_repository import RelationshipInviteNotFoundError
from app.api.repositories.relationship_repository import (
    DuplicateEntryError,
    RelationshipMemberNotFoundError,
    RelationshipNotFoundError,
    UserNotAMemberOfRelationshipError,
)
from app.api.repositories.user_repository import UserNotFoundError
from app.api.schemas.relationship_schema import (
    RelationshipCreate,
    RelationshipSchema,
    RelationshipUpdate,
)
from app.api.schemas.user_schema import PartnerSchema
from app.api.services.relationship_invites_service import (
    InviteExpiredError,
    RelationshipInvitesService,
)
from app.api.services.relationships_service import InvalidInviteUserError, RelationshipsService
from app.api.services.users_service import UsersService

router = APIRouter()
relationship_service_dependency = Depends(get_relationships_service)
relationship_invite_service_dependency = Depends(get_relationship_invites_service)
users_service_dependency = Depends(get_users_service)
get_current_user_dependency = Depends(get_current_user)


@router.post(
    "/relationships", status_code=status.HTTP_201_CREATED, response_model=RelationshipSchema
)
async def add_relationship(
    relationship_info: RelationshipCreate,
    service: RelationshipsService = relationship_service_dependency,
    users_service: UsersService = users_service_dependency,
    relationship_invite_service: RelationshipInvitesService = relationship_invite_service_dependency,
    current_user=get_current_user_dependency,
):
    try:
        relationship = await service.add(
            current_user, relationship_info, users_service, relationship_invite_service
        )
        return relationship
    except RelationshipInviteNotFoundError as e:
        raise HTTPException(status_code=404, detail={"message": str(e)}) from e
    except InviteExpiredError as e:
        raise HTTPException(status_code=410, detail={"message": str(e)}) from e
    except InvalidInviteUserError as e:
        raise HTTPException(status_code=403, detail={"message": str(e)}) from e
    except DuplicateEntryError as e:
        raise HTTPException(status_code=409, detail={"message": str(e)}) from e


@router.get("/relationships", response_model=RelationshipSchema)
async def get_my_relationship(
    service: RelationshipsService = relationship_service_dependency,
    current_user=get_current_user_dependency,
):
    try:
        rel = await service.get_by_user_id(current_user.id)
    except RelationshipMemberNotFoundError as e:
        raise HTTPException(status_code=404, detail={"message": str(e)}) from e
    except RelationshipNotFoundError as e:
        raise HTTPException(status_code=404, detail={"message": str(e)}) from e
    return rel


@router.get("/relationships/partner", response_model=PartnerSchema)
async def get_partner(
    service: RelationshipsService = relationship_service_dependency,
    current_user=get_current_user_dependency,
):
    try:
        partner = await service.get_partner(current_user)
    except (RelationshipMemberNotFoundError, UserNotFoundError) as e:
        raise HTTPException(status_code=404, detail={"message": str(e)}) from e
    return partner


@router.get("/relationships/{id}", response_model=RelationshipSchema)
async def get_relationship(
    id: int,
    service: RelationshipsService = relationship_service_dependency,
    current_user=get_current_user_dependency,
):
    try:
        rel = await service.get_by_id(id, current_user.id)
    except RelationshipNotFoundError as e:
        raise HTTPException(status_code=404, detail={"message": str(e)}) from e
    except UserNotAMemberOfRelationshipError as e:
        raise HTTPException(status_code=401, detail={"message": str(e)}) from e
    return rel


@router.patch("/relationships", response_model=RelationshipSchema)
async def update_relationship(
    update_data: RelationshipUpdate,
    current_user=get_current_user_dependency,
    service: RelationshipsService = relationship_service_dependency,
):
    try:
        relationship = await service.update(current_user.id, update_data)
    except RelationshipMemberNotFoundError as e:
        raise HTTPException(status_code=404, detail={"message": str(e)}) from e
    except RelationshipNotFoundError as e:
        raise HTTPException(status_code=404, detail={"message": str(e)}) from e
    return relationship


@router.delete("/relationships", status_code=status.HTTP_204_NO_CONTENT)
async def delete_relationship(
    current_user=get_current_user_dependency,
    service: RelationshipsService = relationship_service_dependency,
):
    try:
        await service.delete(current_user.id)
    except RelationshipMemberNotFoundError as e:
        raise HTTPException(status_code=404, detail={"message": str(e)}) from e
    except RelationshipNotFoundError as e:
        raise HTTPException(status_code=404, detail={"message": str(e)}) from e
    return Response(status_code=status.HTTP_204_NO_CONTENT)
