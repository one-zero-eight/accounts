__all__ = ["GrantTypes", "ResponseTypes", "UserTokenData"]

from enum import StrEnum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class GrantTypes(StrEnum):
    authorization_code = "authorization_code"


class ResponseTypes(StrEnum):
    code = "code"


class UserTokenData(BaseModel):
    user_id: Optional[int] = None
    scopes: list[str] = Field(default_factory=list)

    @field_validator("user_id", mode="before")
    def cast_to_int(cls, v):
        if isinstance(v, str):
            return int(v)
        return v
