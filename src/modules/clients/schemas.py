from enum import StrEnum

from pydantic import BaseModel, Field

from beanie import PydanticObjectId


class VerificationResultStatus(StrEnum):
    SUCCESS = "success"
    INCORRECT = "incorrect"
    NOT_FOUND = "not_found"


class ClientVerificationResult(BaseModel):
    status: VerificationResultStatus
    client_id: str | None = None


class ClientRead(BaseModel):
    client_id: str
    client_secret: str
    registration_access_token: str | None = None
    registration_client_uri: str | None = None
    owner_id: PydanticObjectId | None = None
    allowed_redirect_uris: list[str] = Field(default_factory=list)


class ClientUpdate(BaseModel):
    allowed_redirect_uris: list[str] | None = None
