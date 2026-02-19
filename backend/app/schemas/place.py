from typing import List, Optional
from pydantic import BaseModel

class PersonAtPlace(BaseModel):
    id: str
    label: str
    type: Optional[str] = None

class PlaceDetail(BaseModel):
    id: str
    uri: str
    label: str
    lat: Optional[str] = None
    long: Optional[str] = None
    people: List[PersonAtPlace] = []

class PlaceList(BaseModel):
    id: str
    uri: str
    label: str
    lat: Optional[str] = None
    long: Optional[str] = None
    personCount: int
