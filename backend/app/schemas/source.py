from typing import Annotated, Optional
from pydantic import BaseModel, StringConstraints, field_validator

NonEmpty = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
OptionalText = Optional[Annotated[str, StringConstraints(strip_whitespace=True)]]

class SourceInput(BaseModel):
    name: NonEmpty
    shelfmark: OptionalText = None
    url: OptionalText = None

    @field_validator("shelfmark", "url")
    @classmethod
    def empty_to_none(cls, value: Optional[str]) -> Optional[str]:
        return value or None

    @field_validator("url")
    @classmethod
    def check_url(cls, value: Optional[str]) -> Optional[str]:
        if value and not value.startswith(("http://", "https://")):
            raise ValueError("Link must start with http:// or https://")
        return value

class SourceDetail(BaseModel):
    id: str
    label: str
    shelfmark: Optional[str] = None
    url: Optional[str] = None
