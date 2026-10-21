from typing import Annotated, List, Optional
from pydantic import BaseModel, Field, StringConstraints

class PersonAtPlace(BaseModel):
    id: str
    label: str
    type: Optional[str] = None

class PlaceDetail(BaseModel):
    id: str
    label: str
    lat: Optional[str] = None
    long: Optional[str] = None
    people: List[PersonAtPlace] = []

class PlaceList(BaseModel):
    id: str
    label: str
    lat: Optional[str] = None
    long: Optional[str] = None
    personCount: int

class PlaceInput(BaseModel):
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    lat: float = Field(ge=-90, le=90)
    long: float = Field(ge=-180, le=180)
