import os
from dotenv import load_dotenv
load_dotenv()
def db_url():
    return os.getenv("DATABASE_URL")
