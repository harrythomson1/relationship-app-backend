import os

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from app.api.auth.utils import get_current_user
from app.api.dependencies import get_relationship_invites_service
from app.api.repositories.relationship_invite_repository import DuplicateInviteError
from app.api.schemas.relationship_invite_schema import (
    RelationshipInviteCreate,
    RelationshipInviteSchema,
)
from app.api.services.relationship_invites_service import RelationshipInvitesService
from app.api.utils import mailer

router = APIRouter(prefix="/relationships", tags=["relationships"])

relationship_invite_service_dependency = Depends(get_relationship_invites_service)
get_current_user_dependency = Depends(get_current_user)


@router.post(
    "/invites", status_code=status.HTTP_201_CREATED, response_model=RelationshipInviteSchema
)
async def add_relationship_invite(
    relationship_invite_info: RelationshipInviteCreate,
    background: BackgroundTasks,
    service: RelationshipInvitesService = relationship_invite_service_dependency,
    current_user=get_current_user_dependency,
):
    try:
        relationship_invite = await service.add(relationship_invite_info, current_user)
        html_content = """
<p>Hello, I want to add you to the relationship.</p>
<p>
Please follow this link to accept:
<a href="relationshipappfrontend://profile">Open in app</a> relationshipappfrontend://profile
</p>
"""
        background.add_task(
            mailer.send_email,
            sender=os.environ.get("APP_EMAIL"),
            receiver=relationship_invite_info.invitee_email,
            subject="Let's connect",
            content=html_content,
        )
        return relationship_invite
    except DuplicateInviteError as e:
        raise HTTPException(status_code=409, detail={"message": str(e)}) from e
