import asyncio
import logging
import os
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.core.database_connection import SessionLocal
from app.api.jobs.overlap_notifier import notify_imminent_overlaps
from app.api.routes import (
    invites,
    me,
    notification_preferences,
    push_tokens,
    relationships,
    users,
)

logger = logging.getLogger(__name__)

OVERLAP_NOTIFIER_INTERVAL_SECONDS = int(os.getenv("OVERLAP_NOTIFIER_INTERVAL_SECONDS", "60"))
OVERLAP_NOTIFIER_ENABLED = os.getenv("OVERLAP_NOTIFIER_ENABLED", "true").lower() == "true"


async def _overlap_notifier_loop():
    while True:
        try:
            async with SessionLocal() as session:
                await notify_imminent_overlaps(session)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("overlap notifier tick failed")
        await asyncio.sleep(OVERLAP_NOTIFIER_INTERVAL_SECONDS)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    task: asyncio.Task | None = None
    if OVERLAP_NOTIFIER_ENABLED:
        task = asyncio.create_task(_overlap_notifier_loop())
    try:
        yield
    finally:
        if task is not None:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task


app = FastAPI(title="Relationship App API", version="0.1.0", lifespan=lifespan)

origins = (
    [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]
    if os.getenv("CORS_ORIGINS")
    else ["*"]
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)
app.include_router(me.router)
app.include_router(users.router)
app.include_router(invites.router)
app.include_router(relationships.router)
app.include_router(push_tokens.router)
app.include_router(notification_preferences.router)


@app.get("/health")
def health():
    return {"status": "ok"}
