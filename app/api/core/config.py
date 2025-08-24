import os
from typing import Final

from dotenv import load_dotenv

load_dotenv()

_url = os.getenv("DATABASE_URL")
if _url is None:
    raise RuntimeError("DATABASE_URL is not set")

DATABASE_URL: Final[str] = _url
