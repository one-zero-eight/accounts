__all__ = ["UserInfoFromSSO"]

import datetime

from pydantic import BaseModel, Field


class UserInfoFromSSO(BaseModel):
    email: str
    name: str | None = None

    access_token: str = Field(exclude=True)
    refresh_token: str = Field(exclude=True)
    expires_at: datetime.datetime = Field(exclude=True)
    issued_at: datetime.datetime | None = None

    @classmethod
    def from_token_and_userinfo(cls, token: dict, userinfo: dict) -> "UserInfoFromSSO":
        return UserInfoFromSSO(
            access_token=token["access_token"],
            refresh_token=token["refresh_token"],
            email=userinfo["email"],
            name=userinfo.get("commonname"),
            issued_at=datetime.datetime.fromtimestamp(userinfo["iat"]) if "iat" in userinfo else None,
            expires_at=token["expires_at"],
        )
