from typing import List, Optional
from pydantic import BaseModel

class WorkAuthor(BaseModel):
    id: str
    uri: str
    label: str

class ScholarlyWorkRef(BaseModel):
    id: str
    uri: str
    title: str
    year: Optional[str] = None

from app.schemas.person import PlaceRelation, TimeRelation

class WorkDetail(BaseModel):
    id: str
    uri: str
    title: str
    sources: List[str] = []
    authors: List[WorkAuthor] = []
    subjects: List[str] = []
    languages: List[str] = []
    scholarly_mentions: List[ScholarlyWorkRef] = []
    places: List[PlaceRelation] = []
    times: List[TimeRelation] = []

class WorkList(BaseModel):
    id: str
    uri: str
    title: str
    creation_year: Optional[str] = None
    authors: Optional[str] = None
    subjects: Optional[str] = None
    languages: Optional[str] = None
