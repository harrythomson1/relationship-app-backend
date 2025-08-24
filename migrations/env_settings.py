import os
from dotenv import load_dotenv
load_dotenv()
def db_url() -> str:
    url = os.getenv("DATABASE_URL")
    if url is None:
        raise RuntimeError("DATABASE_URL is not set")
    return url
