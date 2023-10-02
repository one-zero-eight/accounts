__all__ = ["UserInfoFromSSO", "ViewUser"]

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator
import datetime


class UserInfoFromSSO(BaseModel):
    email: str
    access_token: str = Field(..., exclude=True)
    refresh_token: str = Field(..., exclude=True)

    status: Optional[list[str]] = Field(default_factory=list)
    name: Optional[str] = None

    updated_at: Optional[datetime.datetime] = None
    created_at: Optional[datetime.datetime] = None

    @field_validator("status", mode="before")
    def _validate_status(cls, v):
        if isinstance(v, str):
            return [v]
        if v is None:
            return []
        return v


class ViewUser(BaseModel):
    """
    Represents a user instance from the database excluding sensitive information such as password.
    """

    id: int
    innopolis_sso: Optional["UserInfoFromSSO"] = None
    model_config = ConfigDict(from_attributes=True)
