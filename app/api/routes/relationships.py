from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_relationships_service
from app.api.repositories.relationship_repository import RelationshipNotFoundError
from app.api.schemas.relationship_schema import RelationshipCreate, RelationshipSchema
from app.api.services.relationships_service import RelationshipsService

router = APIRouter()
relationship_service_dependency = Depends(get_relationships_service)


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
