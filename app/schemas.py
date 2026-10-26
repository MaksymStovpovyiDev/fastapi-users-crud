from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, StringConstraints, model_validator

Name = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)
]


class UserCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Name
    email: EmailStr


class UserUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Name | None = None
    email: EmailStr | None = None

    @model_validator(mode="after")
    def check_changes(self):
        if not self.model_fields_set:
            raise ValueError("Provide name or email")
        if any(getattr(self, field) is None for field in self.model_fields_set):
            raise ValueError("Name and email cannot be null")
        return self


class User(BaseModel):
    id: int
    name: str
    email: EmailStr
    created_at: datetime
