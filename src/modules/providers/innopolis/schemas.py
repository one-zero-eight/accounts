__all__ = ["UserInfoFromSSO"]

import datetime

from pydantic import BaseModel, Field, field_validator


class UserInfoFromSSO(BaseModel):
    email: str
    access_token: str
    refresh_token: str
    expires_at: datetime.datetime

    status: list[str] | None = Field(default_factory=list)
    name: str | None = None

    @field_validator("status", mode="before")
    def _validate_status(cls, v):
        if isinstance(v, str):
            return [v]
        if v is None:
            return []
        return v

    @classmethod
    def from_token_and_userinfo(cls, token: dict, userinfo: dict) -> "UserInfoFromSSO":
        return cls(
            access_token=token["access_token"],
            refresh_token=token["refresh_token"],
            email=userinfo["email"],
            name=userinfo.get("commonname"),
            status=userinfo.get("Status"),
            expires_at=token["expires_at"],
        )
