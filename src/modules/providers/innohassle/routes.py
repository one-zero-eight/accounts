import httpx
from fastapi import APIRouter, Request

from src.config import settings
from src.config_schema import Environment
from src.exceptions import ObjectNotFound
from src.storages.mongo.models import User

router = APIRouter(prefix="/innohassle")

if settings.accounts:
    if settings.environment == Environment.PRODUCTION:
        raise NotImplementedError("InNoHassle Accounts Provider is not available in production")

    accounts = settings.accounts

    @router.post(
        "/login",
        responses={
            200: {"description": "Success"},
        },
    )
    async def innohassle_accounts_login(user_id: str, request: Request):
        """
        Login as any user from InNoHassle Accounts, see [InNoHassle Accounts API](https://api.innohassle.ru/accounts/v0/docs#/Users/users_get_me).
        """
        request.session.clear()
        user_from_innohassle_accounts = await get_innohassle_user(user_id)
        if user_from_innohassle_accounts is None:
            raise ObjectNotFound("User not found")
        user = User.model_validate(user_from_innohassle_accounts, from_attributes=True)

        # check for existence of user in current database
        # if not found, create user
        exists = await User.find_one(User.id == user.id).count()
        if not exists:
            await user.insert()

        request.session["uid"] = str(user.id)

    async def get_innohassle_user(user_id: str) -> User | None:
        async with get_authorized_client() as client:
            response = await client.get(f"{accounts.api_url}/users/by-id/{user_id}")
            try:
                response.raise_for_status()
                return User.model_validate(response.json())
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    return None
                raise e

    def get_authorized_client() -> httpx.AsyncClient:
        return httpx.AsyncClient(headers={"Authorization": f"Bearer {accounts.api_jwt_token.get_secret_value()}"})
