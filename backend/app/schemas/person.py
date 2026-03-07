from typing import List, Optional
from pydantic import BaseModel

class AuthorityLink(BaseModel):
    uri: str

class RelatedWork(BaseModel):
    id: str
    uri: str
    title: str

class ScholarlyMention(BaseModel):
    id: str
    uri: str
    title: str
    year: Optional[str] = None

class PlaceRelation(BaseModel):
    place_id: str
    place_uri: str
    label: str
    type: Optional[str] = None

class TimeRelation(BaseModel):
    type: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None

class PersonDetail(BaseModel):
    id: str
    uri: str
    label: str
    sources: List[str] = []  # Source attributions (e.g., "Wikidata")
    authorities: List[str] = []
    works: List[RelatedWork] = []
    scholarly: List[ScholarlyMention] = []
    places: List[PlaceRelation] = []
    times: List[TimeRelation] = []
    subjects: List[str] = []
    languages: List[str] = []

class PersonList(BaseModel):
    id: str
    uri: str
    label: str
    birth_year: Optional[str] = None
    death_year: Optional[str] = None
    places: Optional[str] = None
    times: Optional[str] = None
