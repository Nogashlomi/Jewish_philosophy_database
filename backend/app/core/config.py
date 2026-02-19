import os

class Settings:
    APP_NAME = "JPO Research Explorer"
    VERSION = "0.1.0"
    # Base dir is the backend/ directory
    # file is backend/app/core/config.py
    # parent -> backend/app/core
    # parent -> backend/app
    # parent -> backend
    BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    # Data is in sibling of backend: ../data
    PROJECT_ROOT = os.path.dirname(BACKEND_DIR)
    
    DATA_DIR = os.path.join(PROJECT_ROOT, "data")
    ONTOLOGY_DIR = os.path.join(PROJECT_ROOT, "data/ontology")

settings = Settings()
