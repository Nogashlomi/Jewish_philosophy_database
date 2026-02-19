from typing import List, Optional
from pydantic import BaseModel

class MentionedPerson(BaseModel):
    id: str
    label: str

class MentionedWork(BaseModel):
    id: str
    title: str

class Scholar(BaseModel):
    id: str
    name: str

class Source(BaseModel):
    id: str
    label: str

class ScholarlyDetail(BaseModel):
    uri: str
    title: str
    year: Optional[str] = None
    authors: List[Scholar] = []
    source: Optional[Source] = None
    mentions_person: List[MentionedPerson] = []
    mentions_work: List[MentionedWork] = []

class ScholarlyList(BaseModel):
    uri: str
    id: str
    title: str
    year: Optional[str] = None
    authors: List[Scholar] = []
    source: Optional[Source] = None
    publisher: Optional[str] = None
    type: Optional[str] = None
    mentions_person_count: int = 0
    mentions_work_count: int = 0
