__all__ = ["UserInfoFromSSO"]

import datetime

from pydantic import BaseModel, Field

from src.logging_ import logger


class UserInfoFromSSO(BaseModel):
    email: str
    name: str | None = None

    access_token: str | None = Field(None, exclude=True)
    refresh_token: str | None = Field(None, exclude=True)
    expires_at: datetime.datetime | None = Field(None, exclude=True)
    issued_at: datetime.datetime | None = None
    is_student: bool = False
    is_staff: bool = False
    group: str | None = None

    @classmethod
    def from_token_and_userinfo(cls, token: dict, userinfo: dict) -> "UserInfoFromSSO":
        status = userinfo.get("Status")
        if isinstance(status, str):
            status = [status]
        status: list[str]
        is_student = is_staff = False
        if status:
            if "Student" in status:
                is_student = True

            if "Staff" in status:
                is_staff = True

            if not is_student and not is_staff:
                logger.warning(f"Neither student or staff: {status}")
        else:
            logger.warning(f"Status is empty for {userinfo['email']}: {status}")
        return UserInfoFromSSO(
            access_token=token["access_token"],
            refresh_token=token["refresh_token"],
            email=userinfo["email"],
            name=userinfo.get("commonname"),
            issued_at=datetime.datetime.fromtimestamp(userinfo["iat"]) if "iat" in userinfo else None,
            expires_at=token["expires_at"],
            is_student=is_student,
            is_staff=is_staff,
            group=userinfo.get("group"),
        )
