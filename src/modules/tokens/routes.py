from fastapi import APIRouter
from pydantic import BaseModel

from src.api.dependencies import AdminDep, UserDep
from src.exceptions import UserWithoutSessionException, NotEnoughPermissionsException
from src.modules.tokens.repository import TokenRepository

router = APIRouter(tags=["Tokens"])


class TokenData(BaseModel):
    access_token: str


@router.get("/.well-known/jwks.json")
async def get_jwks():
    """
    Get jwks for jwt
    """
    return TokenRepository.get_jwks()


@router.get(
    "/tokens/generate-access-token",
    responses={
        200: {"description": "Token"},
        **UserWithoutSessionException.responses,
        **NotEnoughPermissionsException.responses,
    },
)
async def generate_token(_user: AdminDep, sub: str) -> TokenData:
    """
    Generate access token with some sub in `sub` field
    """
    token = TokenRepository.create_access_token(sub)
    return TokenData(access_token=token)


@router.get(
    "/tokens/generate-my-token",
    responses={200: {"description": "Token"}, **UserWithoutSessionException.responses},
    response_model=TokenData,
)
async def generate_my_token(user: UserDep) -> TokenData:
    """
    Generate access token for current user with user id in `uid` field
    """
    token = TokenRepository.create_user_access_token(user.id)
    return TokenData(access_token=token)
