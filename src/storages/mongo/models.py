from pydantic import BaseModel

from src.modules.providers.innopolis.schemas import UserInfoFromSSO
from src.modules.providers.telegram.schemas import TelegramWidgetData
from src.modules.telegram_update.schemas import TelegramUpdateData
from src.storages.mongo.__base__ import CustomDocument


class UserSchema(BaseModel):
    innopolis_sso: UserInfoFromSSO | None = None
    telegram: TelegramWidgetData | None = None
    telegram_update_data: TelegramUpdateData | None = None
    innohassle_admin: bool = False

    @property
    def is_admin(self) -> bool:
        return self.innohassle_admin


class User(UserSchema, CustomDocument):
    pass


document_models = [User]
