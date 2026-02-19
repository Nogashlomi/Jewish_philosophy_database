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

class WorkDetail(BaseModel):
    id: str
    uri: str
    title: str
    authors: List[WorkAuthor] = []
    subjects: List[str] = []
    languages: List[str] = []
    scholarly_mentions: List[ScholarlyWorkRef] = []

class WorkList(BaseModel):
    id: str
    uri: str
    title: str
    authors: str
    mentionCount: int
