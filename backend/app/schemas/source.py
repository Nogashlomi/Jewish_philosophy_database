from typing import Optional
from pydantic import BaseModel

class Source(BaseModel):
    id: str
    label: str
    description: Optional[str] = None
    count: int
