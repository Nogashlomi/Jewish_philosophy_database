from typing import Annotated, List, Literal, Optional
from pydantic import BaseModel, Field, StringConstraints, model_validator

ConnectionType = Literal["birth", "death", "burial", "lifespan", "activity", "residence", "study", "travel", "associated"]
OptionalText = Optional[Annotated[str, StringConstraints(strip_whitespace=True)]]

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
    estimated: bool = False
    description: Optional[str] = None
    source: Optional[str] = None

class IntellectualRelation(BaseModel):
    id: str
    label: str
    entity_type: str
    relation: str

class TimeRelation(BaseModel):
    type: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None
    estimated: bool = False
    description: Optional[str] = None
    source: Optional[str] = None

class PersonConnectionInput(BaseModel):
    type: ConnectionType
    place_id: Optional[str] = None
    start: Optional[int] = None
    end: Optional[int] = None
    estimated: bool = False
    description: OptionalText = None
    source_id: Optional[str] = None

    @model_validator(mode="after")
    def check_place_or_time(self):
        self.description = self.description or None
        if self.place_id is None and self.start is None:
            raise ValueError("A connection needs a place, a start year, or both")
        if self.end is not None and self.start is None:
            raise ValueError("An end year requires a start year")
        if self.end is not None and self.end < self.start:
            raise ValueError("End year must not be before start year")
        return self

class PersonConnection(PersonConnectionInput):
    place_label: Optional[str] = None
    source_label: Optional[str] = None

class UpdateConnections(BaseModel):
    connections: List[PersonConnectionInput]

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
    connections: List[PersonConnection] = []
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
