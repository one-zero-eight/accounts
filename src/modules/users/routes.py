"""
User data and linking users with event groups.
"""

from typing import Annotated

from authlib.jose import JWTClaims
from beanie import PydanticObjectId
from fastapi import APIRouter, Request, Security

from src.api import docs
from src.api.dependencies import UserIdDep
from src.exceptions import ObjectNotFound, UserWithoutSessionException
from src.modules.tokens.dependencies import verify_access_token, verify_access_token_responses
from src.modules.users.repository import user_repository
from src.storages.mongo.models import User

router = APIRouter(prefix="/users", tags=["Users"])
docs.TAGS_INFO.append({"description": __doc__, "name": str(router.tags[0])})


UsersScopeDep = Annotated[JWTClaims, Security(verify_access_token, scopes=["users"])]


@router.get(
    "/me",
    responses={200: {"description": "Current user info"}, **UserWithoutSessionException.responses},
)
async def get_me(user_id: UserIdDep, request: Request) -> User:
    """
    Get current user info if authenticated
    """
    user = await user_repository.read(user_id)
    if user is None:
        # clear session cookie if user is not found
        request.session.clear()
        raise UserWithoutSessionException()
    return user


def allowed_user_id_for_jwt_claims(user_id: PydanticObjectId, jwt_claims: JWTClaims) -> bool:
    scope_string = jwt_claims.get("scope", "")
    scopes = scope_string.split() if scope_string else []
    users_scopes = [scope for scope in scopes if scope.startswith("users")]
    if "users" in users_scopes:  # wildcard
        return True

    if f"users:{user_id}" in users_scopes:
        return True

    return False


@router.get(
    "/by-telegram-id/{telegram_id}",
    response_model=User,
    responses={200: {"description": "User info"}, **ObjectNotFound.responses, **verify_access_token_responses},
)
async def get_user_by_telegram_id(telegram_id: int, jwt_claims: UsersScopeDep) -> User:
    """
    Get user by telegram id
    """

    user = await user_repository.read_by_telegram_id(telegram_id)
    if user is None or not allowed_user_id_for_jwt_claims(user.id, jwt_claims):
        raise ObjectNotFound("User not found")

    return user


@router.get(
    "/by-id/{user_id}",
    response_model=User,
    responses={200: {"description": "User info"}, **ObjectNotFound.responses, **verify_access_token_responses},
)
async def get_user_by_id(user_id: PydanticObjectId, jwt_claims: UsersScopeDep) -> User:
    """
    Get user by id
    """
    user = await user_repository.read(user_id)
    if user is None or not allowed_user_id_for_jwt_claims(user.id, jwt_claims):
        raise ObjectNotFound("User not found")
    return user


@router.get(
    "/by-innomail/{email}",
    response_model=User,
    responses={200: {"description": "User info"}, **ObjectNotFound.responses, **verify_access_token_responses},
)
async def get_user_by_innomail(email: str, jwt_claims: UsersScopeDep) -> User:
    """
    Get user by email
    """
    user = await user_repository.read_by_innomail(email)
    if user is None or not allowed_user_id_for_jwt_claims(user.id, jwt_claims):
        raise ObjectNotFound("User not found")
    return user
