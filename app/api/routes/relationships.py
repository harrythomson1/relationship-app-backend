from fastapi import APIRouter, Depends, HTTPException, status

from app.api.auth.utils import get_current_user
from app.api.dependencies import get_relationships_service
from app.api.repositories.relationship_repository import (
    RelationshipMemberNotFoundError,
    RelationshipNotFoundError,
)
from app.api.schemas.relationship_schema import (
    RelationshipCreate,
    RelationshipSchema,
    RelationshipUpdate,
)
from app.api.services.relationships_service import RelationshipsService

router = APIRouter()
relationship_service_dependency = Depends(get_relationships_service)
get_current_user_dependency = Depends(get_current_user)


@router.post(
    "/relationships", status_code=status.HTTP_201_CREATED, response_model=RelationshipSchema
)
async def add_relationship(
    relationship_info: RelationshipCreate,
    service: RelationshipsService = relationship_service_dependency,
):
    relationship = await service.add(relationship_info)
    return relationship


@router.get("/relationships/{id}", response_model=RelationshipSchema)
async def get_relationship(
    id: int, service: RelationshipsService = relationship_service_dependency
):
    try:
        rel = await service.get_by_id(id)
    except RelationshipNotFoundError as e:
        raise HTTPException(status_code=404, detail={"message": str(e)}) from e
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
