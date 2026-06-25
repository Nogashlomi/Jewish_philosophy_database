from typing import List, Optional
from pydantic import BaseModel

class AuthorityLink(BaseModel):
    uri: str

class RelatedWork(BaseModel):
    id: str
    uri: str
    title: str

class PlaceRelation(BaseModel):
    place_id: str
    place_uri: str
    label: str
    type: Optional[str] = None

class TimeRelation(BaseModel):
    type: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None
    label: Optional[str] = None

class PersonDetail(BaseModel):
    id: str
    uri: str
    label: str
    works: List[RelatedWork] = []
    places: List[PlaceRelation] = []
    times: List[TimeRelation] = []
    time_buckets: List[str] = []
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
    time_buckets: Optional[str] = None
    subjects: Optional[str] = None
