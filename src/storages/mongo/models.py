import datetime
from enum import StrEnum
from typing import Annotated

from beanie import Indexed
from pydantic import Field, BaseModel

from src.modules.providers.innopolis.schemas import UserInfoFromSSO
from src.modules.providers.telegram.schemas import TelegramWidgetData
from beanie import PydanticObjectId
from src.storages.mongo.__base__ import CustomDocument


class ClientType(StrEnum):
    public = "public"
    confidential = "confidential"


class Client(CustomDocument):
    client_id: Annotated[str, Indexed(unique=True)]
    client_secret: str | None = None
    client_type: ClientType = ClientType.confidential
    registration_access_token: str
    owner_id: PydanticObjectId | None = None
    allowed_redirect_uris: list[str] = Field(default_factory=list)
    approved: bool = False


class EmailFlow(CustomDocument):
    email: str
    is_sent: bool = False
    sent_at: datetime.datetime | None = None
    is_verified: bool = False
    verified_at: datetime.datetime | None = None
    verification_code: str | None = None
    verification_code_expires_at: datetime.datetime | None = None
    user_id: PydanticObjectId | None = None
    client_id: str | None = None


class User(CustomDocument):
    innopolis_sso: UserInfoFromSSO | None = None
    telegram: TelegramWidgetData | None = None


class ScopeSettings(BaseModel):
    allowed_for_all: bool = False
    clients_allowed_for: list[str] = Field(default_factory=list)


class Resource(CustomDocument):
    resource_id: Annotated[str, Indexed(unique=True)]
    scopes: dict[str, ScopeSettings | None] = Field(default_factory=dict)
    owner_id: PydanticObjectId


document_models = [
    User,
    Resource,
    Client,
    EmailFlow,
]
