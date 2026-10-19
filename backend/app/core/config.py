import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Medieval Jewish Philosophy Database"
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"

    # CORS configuration
    ALLOWED_ORIGINS: str = os.getenv("ALLOWED_ORIGINS", "https://jephy-db.web.app,https://jephy-index.web.app,http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174")

    MONGODB_URI: str
    MONGODB_DB: str = "jephy"
    FIREBASE_PROJECT_ID: str = "jephy-db"

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
