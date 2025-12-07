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
