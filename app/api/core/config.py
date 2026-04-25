import os
from pathlib import Path
from typing import Final

from dotenv import load_dotenv

if Path(".env.local").exists():
    load_dotenv(".env.local", override=True)
else:
    load_dotenv()

_url = os.getenv("DATABASE_URL")
if _url is None:
    raise RuntimeError("DATABASE_URL is not set")

DATABASE_URL: Final[str] = _url

JWKS_URL: str = os.getenv("JWKS_URL", "")
assert JWKS_URL, "JWKS_URL is not set in .env"
PROJECT_URL: str = os.getenv("PROJECT_URL", "")
assert PROJECT_URL, "PROJECT_URL is not set in .env"
AUDIENCE: str = os.getenv("AUDIENCE", "")
assert AUDIENCE, "AUDIENCE is not set in .env"
ALGORITHM: str = os.getenv("ALGORITHM", "")
assert ALGORITHM, "ALGORITHM is not set in .env"
