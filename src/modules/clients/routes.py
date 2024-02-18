from fastapi import APIRouter

from src.api.dependencies import Shared, VerifiedClientIdDep, UserIdDep
from src.modules.clients.repository import ClientRepository

router = APIRouter(prefix="/clients", tags=["Clients"])


@router.get("/me")
async def get_client(client_id: VerifiedClientIdDep):
    client_repository = Shared.f(ClientRepository)
    return await client_repository.read(client_id)


@router.post("/")
async def create_client(user_id: UserIdDep):
    client_repository = Shared.f(ClientRepository)
    client = await client_repository.create()
    await client_repository.set_owner(client.client_id, user_id)
    client.owner_id = user_id
    return client
