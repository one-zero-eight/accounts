__all__ = ["GrantTypes", "ResponseTypes", "UserTokenData"]

from enum import StrEnum
from typing import Optional

from pydantic import BaseModel, Field


class GrantTypes(StrEnum):
    authorization_code = "authorization_code"


class ResponseTypes(StrEnum):
    code = "code"


class UserTokenData(BaseModel):
    user_id: Optional[str] = None
    scopes: list[str] = Field(default_factory=list)
