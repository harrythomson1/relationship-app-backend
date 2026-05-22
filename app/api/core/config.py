import os
from pathlib import Path
from typing import Final

from dotenv import load_dotenv

if Path(".env.local").exists():
    load_dotenv(".env.local", override=True)
else:
    load_dotenv()


def _require_env(name: str) -> str:
    value = os.environ.get(name, "")
    if not value:
        raise RuntimeError(f"{name} is not set in the environment")
    return value


DATABASE_URL: Final[str] = _require_env("DATABASE_URL")
JWKS_URL: Final[str] = _require_env("JWKS_URL")
PROJECT_URL: Final[str] = _require_env("PROJECT_URL")
AUDIENCE: Final[str] = _require_env("AUDIENCE")
ALGORITHM: Final[str] = _require_env("ALGORITHM")
RESEND_API_KEY: Final[str] = _require_env("RESEND_API_KEY")
SUPABASE_SERVICE_ROLE_KEY: Final[str] = _require_env("SUPABASE_SERVICE_ROLE_KEY")
INVITE_ACCEPT_BASE_URL: Final[str] = _require_env("INVITE_ACCEPT_BASE_URL")
