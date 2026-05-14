import logging
import os

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.responses import RedirectResponse

from app.api.auth.utils import get_current_user
from app.api.dependencies import get_relationship_invites_service
from app.api.repositories.relationship_invite_repository import (
    DuplicateInviteError,
    RelationshipInviteNotFoundError,
)
from app.api.schemas.relationship_invite_schema import (
    RelationshipInviteCreate,
    RelationshipInviteSchema,
)
from app.api.services.relationship_invites_service import (
    InviteExpiredError,
    InviteRecipientMismatchError,
    RelationshipInvitesService,
)
from app.api.utils import mailer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/relationships", tags=["relationships"])

relationship_invite_service_dependency = Depends(get_relationship_invites_service)
get_current_user_dependency = Depends(get_current_user)

BASE_URL = os.environ.get(
    "INVITE_ACCEPT_BASE_URL", "https://relationship-app-backend-production.up.railway.app"
)


async def _send_invite_email_safely(sender, receiver, subject, content):
    try:
        await mailer.send_email(sender=sender, receiver=receiver, subject=subject, content=content)
    except Exception:
        logger.exception(
            "Failed to send invite email to %s", receiver, extra={"receiver": receiver}
        )


@router.get("/invites/accept")
async def accept_relationship_invite(token: str):
    return RedirectResponse(url=f"anywhere://profile?token={token}")


@router.put("/invites/{token}/decline", status_code=status.HTTP_204_NO_CONTENT)
async def decline_relationship_invite(
    token: str,
    service: RelationshipInvitesService = relationship_invite_service_dependency,
    current_user=get_current_user_dependency,
):
    try:
        await service.mark_declined(token, current_user)
    except RelationshipInviteNotFoundError as e:
        raise HTTPException(status_code=404, detail={"message": str(e)}) from e
    except InviteRecipientMismatchError as e:
        raise HTTPException(status_code=403, detail={"message": str(e)}) from e
    except InviteExpiredError as e:
        raise HTTPException(status_code=410, detail={"message": str(e)}) from e


@router.get("/invites/pending", response_model=RelationshipInviteSchema | None)
async def get_pending_invite(
    service: RelationshipInvitesService = relationship_invite_service_dependency,
    current_user=get_current_user_dependency,
):
    return await service.get_pending_for_user(current_user)


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
        accept_url = f"{BASE_URL}/relationships/invites/accept?token={relationship_invite.token}"
        html_content = f"""
<p>Hello, you've been invited to connect on Anywhere.</p>
<p><a href="{accept_url}">Tap here to accept</a></p>
"""
        background.add_task(
            _send_invite_email_safely,
            sender=os.environ.get("APP_EMAIL"),
            receiver=relationship_invite_info.invitee_email,
            subject="Let's connect",
            content=html_content,
        )
        return relationship_invite
    except DuplicateInviteError as e:
        raise HTTPException(status_code=409, detail={"message": str(e)}) from e
