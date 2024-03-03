import secrets

from beanie import PydanticObjectId
from beanie.odm.operators.update.general import Set
from pydantic import SecretStr

from src.modules.clients.schemas import VerificationResultStatus, ClientVerificationResult, ClientUpdate
from src.storages.mongo.models import Client


def _generate_random_secret() -> SecretStr:
    return SecretStr(secrets.token_urlsafe(32))


def _generate_random_registration_access_token() -> str:
    return f"reg_{secrets.token_urlsafe(32)}.{secrets.token_urlsafe(6)}"


# noinspection PyMethodMayBeStatic
class ClientRepository:
    async def create(self) -> Client:
        # generate random id
        async def _generate_random_id() -> str:
            random_id = secrets.token_urlsafe(8)
            while await Client.find_many(Client.client_id == random_id).count() > 0:
                random_id = secrets.token_urlsafe(8)
            return random_id

        client_id = await _generate_random_id()
        client_secret = _generate_random_secret()
        registration_access_token = _generate_random_registration_access_token()

        client = Client(
            client_id=client_id,
            client_secret=client_secret.get_secret_value(),
            registration_access_token=registration_access_token,
        )
        await client.save()
        return client

    async def read(self, client_id: str) -> Client | None:
        client = await Client.find_one(Client.client_id == client_id)
        return client

    async def update(self, client_id: str, client_update: ClientUpdate) -> Client | None:
        obj = await self.read(client_id)
        if obj is None:
            return None

        updated = await obj.update(Set(client_update.model_dump(exclude_unset=True)))
        return updated

    async def verify(self, client_id: str, client_secret: str) -> ClientVerificationResult:
        client = await self.read(client_id)

        if client is None:
            return ClientVerificationResult(status=VerificationResultStatus.NOT_FOUND)

        if client_secret == client.client_secret:
            return ClientVerificationResult(status=VerificationResultStatus.SUCCESS, client_id=client.client_id)

        return ClientVerificationResult(status=VerificationResultStatus.INCORRECT)

    async def set_owner(self, client_id: str, owner_id: PydanticObjectId) -> None:
        await Client.update_one(Client.client_id == client_id, Set({Client.owner_id: owner_id}))


client_repository = ClientRepository()
