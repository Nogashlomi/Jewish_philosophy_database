from typing import List, Optional
from pydantic import BaseModel, Field

class ViafSuggestion(BaseModel):
    viaf_id: str
    viaf_name: str
    name: str

class VerifyName(BaseModel):
    name: Optional[str] = Field(None, min_length=1)
    viaf_id: Optional[str] = Field(None, pattern=r"^\d+$")
    alt_names: Optional[List[str]] = None

class RelatedWork(BaseModel):
    id: str
    title: str

class PlaceRelation(BaseModel):
    place_id: str
    label: str
    type: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None
    time_label: Optional[str] = None
    description: Optional[str] = None

class IntellectualRelation(BaseModel):
    id: str
    label: str
    entity_type: str
    relation: str

class TimeRelation(BaseModel):
    type: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None
    label: Optional[str] = None

class PersonDetail(BaseModel):
    id: str
    label: str
    alt_names: List[str] = []
    name_verified: bool = False
    viaf_id: Optional[str] = None
    viaf_suggestions: List[ViafSuggestion] = []
    works: List[RelatedWork] = []
    places: List[PlaceRelation] = []
    times: List[TimeRelation] = []
    time_buckets: List[str] = []
    subjects: List[str] = []
    languages: List[str] = []
    relations: List[IntellectualRelation] = []

class PersonList(BaseModel):
    id: str
    label: str
    name_verified: bool = False
    viaf_id: Optional[str] = None
    viaf_suggestions: List[ViafSuggestion] = []
    places: Optional[str] = None
    times: Optional[str] = None
    time_buckets: Optional[str] = None
    subjects: Optional[str] = None
