import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    BLACKBOX_API_KEY: str = os.getenv("BLACKBOX_API_KEY")
    BLACKBOX_BASE_URL: str = os.getenv("BLACKBOX_BASE_URL")

settings = Settings()