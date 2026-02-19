from typing import List
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from app.services.entity_service import entity_service
from app.schemas.place import PlaceList, PlaceDetail

router = APIRouter()

@router.get("/", response_model=List[PlaceList])
async def list_places_json(source: Optional[str] = Query(None, description="Filter by data source ID")):
    """
    Get a list of all places.
    """
    return entity_service.list_places(source=source)

@router.get("/{place_id}", response_model=PlaceDetail)
async def get_place_detail_json(place_id: str):
    """
    Get detailed information about a specific place.
    """
    place = entity_service.get_place_detail(place_id)
    if not place:
        raise HTTPException(status_code=404, detail="Place not found")
    return place

@router.get("/geojson", response_model=dict)
async def get_places_geojson():
    """
    Get all places as a GeoJSON FeatureCollection.
    """
    return entity_service.get_geo_json()
