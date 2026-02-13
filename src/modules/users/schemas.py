import datetime

from beanie import PydanticObjectId
from pydantic import BaseModel, ConfigDict, Field

from src.modules.providers.innopolis.schemas import UserInfoFromSSO
from src.modules.providers.telegram.schemas import TelegramWidgetData
from src.modules.telegram_update.schemas import TelegramUpdateData
from src.storages.mongo.models import User


class TelegramInfo(BaseModel):
    id: int
    first_name: str
    last_name: str | None = None
    username: str | None = None
    photo_url: str | None = None
    updated_at: datetime.datetime


class InnopolisInfo(BaseModel):
    email: str
    name: str | None = None
    is_student: bool = False
    is_staff: bool = False
    is_college: bool = False
    updated_at: datetime.datetime


class UserInfo(BaseModel):
    telegram: TelegramInfo | None = None
    innopolis: InnopolisInfo | None = None


class ViewUser(BaseModel):
    model_config = ConfigDict(use_attribute_docstrings=True)

    id: PydanticObjectId
    innopolis_info: InnopolisInfo | None = None
    telegram_info: TelegramInfo | None = None
    telegram_update_data: TelegramUpdateData | None = None
    innohassle_admin: bool = False

    innopolis_sso: UserInfoFromSSO | None = Field(
        None,
        deprecated=True,
        description="Deprecated field, use `innopolis_info` instead, dont trust data from `innopolis_sso`",
    )
    telegram: TelegramWidgetData | None = Field(
        None,
        deprecated=True,
        description="Deprecated field, use `telegram_info` instead",
    )


def view_from_user(user: User, include_update_data: bool = True, include_deprecated_fields: bool = True) -> "ViewUser":
    id = user.id
    if user.innopolis_sso:
        innopolis_info = InnopolisInfo(
            email=user.innopolis_sso.email,
            name=user.innopolis_sso.name,
            is_student=user.innopolis_sso.is_student,
            is_staff=user.innopolis_sso.is_staff,
            is_college=user.innopolis_sso.is_college,
            updated_at=user.innopolis_sso.issued_at or datetime.datetime.now(datetime.UTC),
        )
    else:
        innopolis_info = None

    if user.telegram:
        telegram_info = TelegramInfo(
            id=user.telegram.id,
            first_name=user.telegram.first_name,
            last_name=user.telegram.last_name,
            username=user.telegram.username,
            photo_url=user.telegram.photo_url,
            updated_at=datetime.datetime.fromtimestamp(user.telegram.auth_date, datetime.UTC),
        )
        if user.telegram_update_data and user.telegram_update_data.success:
            telegram_info.updated_at = datetime.datetime.fromtimestamp(
                user.telegram_update_data.updated_at, datetime.UTC
            )
            if user.telegram_update_data.first_name:  # first_name must be
                telegram_info.first_name = user.telegram_update_data.first_name
            telegram_info.last_name = user.telegram_update_data.last_name
            telegram_info.username = user.telegram_update_data.username
    else:
        telegram_info = None

    return ViewUser(
        id=id,
        innopolis_info=innopolis_info,
        telegram_info=telegram_info,
        telegram_update_data=user.telegram_update_data if include_update_data else None,
        innohassle_admin=user.innohassle_admin,
        # deprecated fields
        innopolis_sso=user.innopolis_sso if include_deprecated_fields else None,
        telegram=user.telegram if include_deprecated_fields else None,
    )
