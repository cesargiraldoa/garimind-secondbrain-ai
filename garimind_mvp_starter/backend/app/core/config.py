import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./garimind.db")
    OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
    TIMEZONE: str = os.getenv("TIMEZONE", "America/Bogota")
    DATA_DIR: str = os.getenv("DATA_DIR", "data/projects")

settings = Settings()
