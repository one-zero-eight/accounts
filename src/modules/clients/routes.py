from fastapi import APIRouter, Request

from src.api.dependencies import Shared, UserIdDep
from src.exceptions import ClientIncorrectCredentialsException
from src.modules.clients.dependencies import ClientRegistrationAccessTokenDep
from src.modules.clients.repository import ClientRepository
from src.modules.clients.schemas import ClientRead, ClientUpdate

router = APIRouter(prefix="/clients", tags=["Clients"])


@router.get("/register/{client_id}", response_model_exclude_unset=True)
async def get_client(client_id: str, registration_access_token: ClientRegistrationAccessTokenDep) -> ClientRead:
    client_repository = Shared.f(ClientRepository)
    client = await client_repository.read(client_id)
    if client is None:
        raise ClientIncorrectCredentialsException()
    if client.registration_access_token != registration_access_token:
        raise ClientIncorrectCredentialsException()

    return ClientRead(
        client_id=client.client_id,
        client_secret=client.client_secret,
        owner_id=client.owner_id,
        # registration_client_uri=str(client.registration_client_uri), # only if changed
        # registration_access_token=client.registration_access_token, # only if changed
        allowed_redirect_uris=client.allowed_redirect_uris,
    )


@router.put("/register/{client_id}", response_model_exclude_unset=True)
async def update_client(
    client_id: str, registration_access_token: ClientRegistrationAccessTokenDep, client_update: ClientUpdate
) -> ClientRead:
    client_repository = Shared.f(ClientRepository)
    client = await client_repository.read(client_id)
    if client is None:
        raise ClientIncorrectCredentialsException()
    if client.registration_access_token != registration_access_token:
        raise ClientIncorrectCredentialsException()

    client = await client_repository.update(client_id, client_update)
    return ClientRead(
        client_id=client.client_id,
        client_secret=client.client_secret,
        owner_id=client.owner_id,
        # registration_client_uri=str(client.registration_client_uri), # only if changed
        # registration_access_token=client.registration_access_token, # only if changed
        allowed_redirect_uris=client.allowed_redirect_uris,
    )


@router.post("/register")
async def create_client(user_id: UserIdDep, request: Request) -> ClientRead:
    client_repository = Shared.f(ClientRepository)
    client = await client_repository.create()
    await client_repository.set_owner(client.client_id, user_id)
    client.owner_id = user_id
    registration_client_uri = request.url_for("get_client", client_id=client.client_id)
    return ClientRead(
        client_id=client.client_id,
        client_secret=client.client_secret,
        owner_id=client.owner_id,
        registration_client_uri=str(registration_client_uri),
        registration_access_token=client.registration_access_token,
        allowed_redirect_uris=client.allowed_redirect_uris,
    )
