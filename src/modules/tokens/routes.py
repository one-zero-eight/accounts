from enum import StrEnum
from typing import Annotated

from authlib.jose import JWTClaims
from beanie import PydanticObjectId
from fastapi import APIRouter, Query, Security
from pydantic import BaseModel

from src.api.dependencies import AdminDep, UserDep
from src.exceptions import InvalidScope, NotEnoughPermissionsException, ObjectNotFound, UserWithoutSessionException
from src.modules.tokens.dependencies import verify_access_token
from src.modules.tokens.repository import TokenRepository
from src.modules.users.repository import user_repository

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
    token = TokenRepository.create_user_access_token(user)
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


class AvailableScopes(StrEnum):
    users = "users"
    sport = "sport"


@router.get(
    "/tokens/generate-service-token",
    responses={
        200: {"description": "Token"},
        **UserWithoutSessionException.responses,
        **NotEnoughPermissionsException.responses,
    },
    response_model=TokenData,
)
async def generate_service_token(
    user: UserDep,
    sub: str = Query(
        ..., description="Some string that will be in `sub` field of JWT token. Actually, it may be anything."
    ),
    scopes: list[AvailableScopes] = Query(
        ["users"], description="List of scopes that will be in `scope` field of JWT token. Default is ['users']"
    ),
    only_for_me: bool = Query(
        True,
        description="Generate token only for current user - other users will be marked as not existing in the system",
    ),
) -> TokenData:
    """
    Generate access token for access users-related endpoints (/users/*).
    """
    _scopes = []

    if not only_for_me and not user.is_admin:
        raise NotEnoughPermissionsException()

    for scope in scopes:
        if scope == AvailableScopes.users:
            _scopes.append(f"users:{user.id}" if only_for_me else "users")
        elif scope == AvailableScopes.sport:
            _scopes.append(f"sport:{user.id}" if only_for_me else "sport")
        else:
            raise InvalidScope(f"Invalid scope: {scope}")

    token = TokenRepository.create_access_token(sub, _scopes)
    return TokenData(access_token=token)


def _allowed_user_id_for_jwt_claims(user_id: PydanticObjectId, jwt_claims: JWTClaims) -> bool:
    scope_string = jwt_claims.get("scope", "")
    scopes = scope_string.split() if scope_string else []
    sport_scopes = [scope for scope in scopes if scope.startswith("sport")]
    if "sport" in sport_scopes:  # wildcard
        return True

    if f"sport:{user_id}" in sport_scopes:
        return True

    return False


SportScopeDep = Annotated[JWTClaims, Security(verify_access_token, scopes=["sport"])]


@router.get(
    "/tokens/generate-sport-token",
    responses={200: {"description": "Token"}, **NotEnoughPermissionsException.responses, **ObjectNotFound.responses},
)
async def generate_sport_token(
    jwt_claims: SportScopeDep,
    telegram_id: int | None = None,
    innohassle_id: PydanticObjectId | None = None,
    email: str | None = None,
) -> TokenData:
    """
    Generate access token for access https://sport.innopolis.university/api/swagger/
    """
    if not any([telegram_id, innohassle_id, email]):
        raise ObjectNotFound("User not found")

    for_user = await user_repository.wild_read(telegram_id=telegram_id, user_id=innohassle_id, email=email)

    if for_user is None:
        raise ObjectNotFound("User not found")

    if not _allowed_user_id_for_jwt_claims(for_user.id, jwt_claims):
        raise NotEnoughPermissionsException()

    if not for_user.innopolis_sso:
        raise ObjectNotFound("User without innopolis_sso email")

    token = TokenRepository.create_sport_user_access_token(for_user.innopolis_sso.email)
    return TokenData(access_token=token)
