import secrets
from enum import StrEnum

from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, SecretStr, Field
from pymongo import ReturnDocument

from src.modules.clients.schemas import VerificationResultStatus, ClientVerificationResult, ClientUpdate
from src.mongo_object_id import PyObjectId


class ClientType(StrEnum):
    public = "public"
    confidential = "confidential"


class Client(BaseModel):
    object_id: PyObjectId = Field(alias="_id")
    client_id: str
    client_secret: str | None = None
    client_type: ClientType = ClientType.confidential
    registration_access_token: str
    owner_id: PyObjectId | None = None
    allowed_redirect_uris: list[str] = Field(default_factory=list)


def _generate_random_secret() -> SecretStr:
    return SecretStr(secrets.token_urlsafe(32))


def _generate_random_registration_access_token() -> str:
    return f"reg_{secrets.token_urlsafe(32)}.{secrets.token_urlsafe(6)}"


class ClientRepository:
    def __init__(self, database: AsyncIOMotorDatabase, *, collection: str = "clients") -> None:
        self.__database = database
        self.__collection = database[collection]

    async def __post_init__(self):
        # unique constraint
        await self.__collection.create_index("client_id", unique=True)

    async def create(self) -> Client:
        # generate random id
        async def _generate_random_id() -> str:
            random_id = secrets.token_urlsafe(8)
            while await self.__collection.count_documents({"client_id": random_id}) > 0:
                random_id = secrets.token_urlsafe(8)
            return random_id

        client_id = await _generate_random_id()
        client_secret = _generate_random_secret()
        registration_access_token = _generate_random_registration_access_token()

        insert_result = await self.__collection.insert_one(
            {
                "client_id": client_id,
                "client_secret": client_secret.get_secret_value(),
                "registration_access_token": registration_access_token,
            }
        )
        client = await self.__collection.find_one({"_id": insert_result.inserted_id})
        return Client.model_validate(client)

    async def read(self, client_id: str) -> Client | None:
        client_dict = await self.__collection.find_one({"client_id": client_id})
        if client_dict is not None:
            return Client.model_validate(client_dict)

    async def update(self, client_id: str, client_update: ClientUpdate) -> Client:
        client_dict = await self.__collection.find_one_and_update(
            {"client_id": client_id},
            {"$set": client_update.model_dump(exclude_unset=True, exclude_none=True)},
            return_document=ReturnDocument.AFTER,
        )
        return Client.model_validate(client_dict)

    async def verify(self, client_id: str, client_secret: str) -> ClientVerificationResult:
        client_dict = await self.__collection.find_one({"client_id": client_id})

        if client_dict is None:
            return ClientVerificationResult(status=VerificationResultStatus.NOT_FOUND)
        client = Client.model_validate(client_dict)

        if client_secret == client.client_secret:
            return ClientVerificationResult(status=VerificationResultStatus.SUCCESS, client_id=client.client_id)

        return ClientVerificationResult(status=VerificationResultStatus.INCORRECT)

    async def set_owner(self, client_id: str, owner_id: PyObjectId) -> None:
        await self.__collection.update_one({"client_id": client_id}, {"$set": {"owner_id": owner_id}})
