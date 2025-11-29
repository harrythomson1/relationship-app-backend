from fastapi import APIRouter, Depends

from app.api.auth.utils import get_current_user
from app.api.dependencies import get_relationships_service
from app.api.schemas.timezone_schema import TimeZoneSchema
from app.api.services.relationships_service import RelationshipsService

router = APIRouter(prefix="/relationships", tags=["relationships"])
get_current_user_dependency = Depends(get_current_user)
relationship_service_dependency = Depends(get_relationships_service)


@router.get("/timezones", response_model=TimeZoneSchema)
async def get_partner_timezone(
    service: RelationshipsService = relationship_service_dependency,
    current_user=get_current_user_dependency,
):
    breakpoint()
    time_zone = await service.get_partner_time_zone(current_user)
