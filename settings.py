import os
import secrets
from dotenv import load_dotenv

load_dotenv(verbose=True)
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    SECRET_KEY = secrets.token_urlsafe(16 * 2)
    with open(".env", "w") as file:
        file.write(f"SECRET_KEY={SECRET_KEY}")


class Config:
    DEBUG = True
    TESTING = True
    SECRET_KEY = SECRET_KEY
