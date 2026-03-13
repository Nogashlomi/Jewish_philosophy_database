import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Medieval Jewish Philosophy Database"
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"

    # CORS configuration
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174"

    # Base dir is the backend/ directory
    # file is backend/app/core/config.py
    # parent -> backend/app/core
    # parent -> backend/app
    # parent -> backend
    BACKEND_DIR: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    # Data is in sibling of backend: ../data
    PROJECT_ROOT: str = os.path.dirname(BACKEND_DIR)

    DATA_DIR: str = os.path.join(PROJECT_ROOT, "data")
    ONTOLOGY_DIR: str = os.path.join(PROJECT_ROOT, "data/ontology")

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
