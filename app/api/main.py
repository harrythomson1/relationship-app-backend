import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import invites, me, push_tokens, relationships, users

app = FastAPI(title="Relationship App API", version="0.1.0")

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


@app.get("/health")
def health():
    return {"status": "ok"}
