from typing import List
from pydantic import BaseModel

class LanguageWorkInfo(BaseModel):
    id: str
    title: str

class LanguageDetail(BaseModel):
    label: str
    works: List[LanguageWorkInfo] = []

class LanguageList(BaseModel):
    id: str
    label: str
    count: int
