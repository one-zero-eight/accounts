from enum import StrEnum

from pydantic import BaseModel, Field

from src.mongo_object_id import PyObjectId


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
    owner_id: PyObjectId | None = None
    allowed_redirect_uris: list[str] = Field(default_factory=list)


class ClientUpdate(BaseModel):
    allowed_redirect_uris: list[str] | None = None
