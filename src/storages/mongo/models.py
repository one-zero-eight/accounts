import datetime

from beanie import PydanticObjectId
from pydantic import BaseModel

from src.modules.providers.innopolis.schemas import UserInfoFromSSO
from src.modules.providers.telegram.schemas import TelegramWidgetData
from src.storages.mongo.__base__ import CustomDocument


class EmailFlowSchema(BaseModel):
    email: str
    is_sent: bool = False
    sent_at: datetime.datetime | None = None
    is_verified: bool = False
    verified_at: datetime.datetime | None = None
    verification_code: str | None = None
    verification_code_expires_at: datetime.datetime | None = None
    user_id: PydanticObjectId | None = None
    client_id: str | None = None


class EmailFlow(EmailFlowSchema, CustomDocument):
    pass


class UserSchema(BaseModel):
    innopolis_sso: UserInfoFromSSO | None = None
    telegram: TelegramWidgetData | None = None
    innohassle_admin: bool = False

    @property
    def is_admin(self) -> bool:
        return self.innohassle_admin


class User(UserSchema, CustomDocument):
    pass


document_models = [User, EmailFlow]
