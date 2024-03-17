import httpx
from fastapi import APIRouter, Request

from src.config import settings
from src.exceptions import ObjectNotFound
from src.storages.mongo.models import User

router = APIRouter(prefix="/innohassle")

if settings.innohassle_accounts:

    @router.post(
        "/login",
        responses={
            200: {"description": "Success"},
        },
    )
    async def innohassle_accounts_login(user_id: str, request: Request):
        request.session.clear()
        user_from_innohassle_accounts = await get_innohassle_user(user_id)
        if user_from_innohassle_accounts is None:
            raise ObjectNotFound("User not found")
        # check for existence of user in current database
        # if not found, create user

        exists = await User.find_one(User.id == user_from_innohassle_accounts.id).count()
        if not exists:
            await user_from_innohassle_accounts.insert()

        request.session["uid"] = str(user_from_innohassle_accounts.id)

    async def get_innohassle_user(user_id: str) -> User | None:
        async with get_authorized_client() as client:
            response = await client.get(f"{settings.innohassle_accounts.api_url}/users/by-id/{user_id}")
            try:
                response.raise_for_status()
                return User.model_validate(response.json())
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    return None
                raise e

    def get_authorized_client() -> httpx.AsyncClient:
        return httpx.AsyncClient(headers={"Authorization": f"Bearer {settings.innohassle_accounts.api_jwt_token}"})
