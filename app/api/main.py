import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import invites, me, relationships, timezones, users

app = FastAPI(title="Relationship App API", version="0.1.0")

origins = os.getenv("CORS_ORIGINS", "").split(",") if os.getenv("CORS_ORIGINS") else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(me.router)
app.include_router(users.router)
app.include_router(timezones.router)
app.include_router(invites.router)
app.include_router(relationships.router)


@app.get("/health")
def health():
    return {"status": "ok"}
