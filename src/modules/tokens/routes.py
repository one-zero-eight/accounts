from fastapi import APIRouter, Query
from pydantic import BaseModel

from src.api.dependencies import UserDep, AdminDep
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


@router.get(
    "/tokens/generate-access-token",
    responses={
        200: {"description": "Token"},
        **UserWithoutSessionException.responses,
        **NotEnoughPermissionsException.responses,
    },
)
async def generate_token(
    _user: AdminDep, sub: str, scope: str | None = Query(None, description="Space delimited list of scopes")
) -> TokenData:
    """
    Generate access token with some sub in `sub` field
    """
    token = TokenRepository.create_access_token(sub, scope.split(" ") if scope else None)
    return TokenData(access_token=token)


@router.get(
    "/tokens/generate-users-scope-service-token",
    responses={
        200: {"description": "Token"},
        **UserWithoutSessionException.responses,
        **NotEnoughPermissionsException.responses,
    },
    response_model=TokenData,
)
async def generate_users_service_token(
    user: UserDep,
    sub: str = Query(
        ..., description="Some string that will be in `sub` field of JWT token. Actually, is may be anything."
    ),
    only_for_me: bool = Query(
        True,
        description="Generate token only for current user - other users will be marked as not existing in the system",
    ),
) -> TokenData:
    """
    Generate access token for access users-related endpoints (/users/*).
    """
    if only_for_me:
        token = TokenRepository.create_access_token(sub, ["users:{}".format(user.id)])
        return TokenData(access_token=token)
    elif user.is_admin:
        token = TokenRepository.create_access_token(sub, ["users"])
        return TokenData(access_token=token)
    else:
        raise NotEnoughPermissionsException()
