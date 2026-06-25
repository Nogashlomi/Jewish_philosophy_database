from typing import List
from pydantic import BaseModel

class LanguagePersonInfo(BaseModel):
    id: str
    name: str

class LanguageDetail(BaseModel):
    label: str
    persons: List[LanguagePersonInfo] = []

class LanguageList(BaseModel):
    id: str
    label: str
    count: int
