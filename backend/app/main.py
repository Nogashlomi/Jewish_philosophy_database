from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.core.rdf_store import rdf_store
from app.core.config import settings
from app.api import (
    persons as api_persons, 
    works as api_works, 
    places as api_places,
    subjects as api_subjects,
    languages as api_languages,
    scholarly as api_scholarly,
    network as api_network,
    sources as api_sources,
    index as api_index,
    ontology as api_ontology
)

# Lifespan Context Manager (Startup/Shutdown)
import contextlib

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up Research Explorer (Lifespan)...")
    try:
        rdf_store.load_data()
        print(f"Graph initialized with {len(rdf_store.g)} triples.")
    except Exception as e:
        print(f"Error loading data: {e}")
    yield
    print("Shutting down Research Explorer...")

# Initialize App with lifespan
app = FastAPI(title=settings.APP_NAME, version=settings.VERSION, lifespan=lifespan)

# CORS Configuration - Allow production and development origins
from fastapi.middleware.cors import CORSMiddleware
import os

# Build CORS origins list from config with fallback to explicit list
config_origins = [origin.strip() for origin in settings.ALLOWED_ORIGINS.split(",")]

# Ensure production Render domains are always included
production_origins = [
    "https://pjh-frontend.onrender.com",
    "https://pjh.onrender.com",
    "https://pjh-frontend-i8oj.onrender.com",
    "https://pjh-backend-i8oj.onrender.com",
]

# Combine: use config origins, but ensure production domains are included
all_origins = list(set(config_origins + production_origins))

print(f"DEBUG: CORS origins configured: {all_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=all_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_index.router, prefix="/api/v1", tags=["api-index"])
app.include_router(api_persons.router, prefix="/api/v1/persons", tags=["api-persons"])
app.include_router(api_works.router, prefix="/api/v1/works", tags=["api-works"])
app.include_router(api_places.router, prefix="/api/v1/places", tags=["api-places"])
app.include_router(api_subjects.router, prefix="/api/v1/subjects", tags=["api-subjects"])
app.include_router(api_languages.router, prefix="/api/v1/languages", tags=["api-languages"])
app.include_router(api_scholarly.router, prefix="/api/v1/scholarly", tags=["api-scholarly"])
app.include_router(api_network.router, prefix="/api/v1/network", tags=["api-network"])
app.include_router(api_sources.router, prefix="/api/v1/sources", tags=["api-sources"])
app.include_router(api_ontology.router, prefix="/api/v1/ontology", tags=["api-ontology"])

# Direct GeoJSON endpoint for Map Component
from app.services.entity_service import entity_service
from fastapi import Query
from typing import Optional

@app.get("/api/v1/geojson")
async def get_geojson_points(source: Optional[str] = Query(None, description="Filter by data source ID")):
    return entity_service.get_geo_json(source=source)
