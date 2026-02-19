from typing import List
from pydantic import BaseModel

class SubjectWorkInfo(BaseModel):
    id: str
    title: str

class SubjectDetail(BaseModel):
    label: str
    works: List[SubjectWorkInfo] = []

class SubjectList(BaseModel):
    id: str
    label: str
    count: int
