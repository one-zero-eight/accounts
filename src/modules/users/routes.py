"""
User data and linking users with event groups.
"""

from typing import Annotated

from authlib.jose import JWTClaims
from beanie import PydanticObjectId
from fastapi import APIRouter, Body, Query, Request, Security

from src.api import docs
from src.api.dependencies import UserIdDep
from src.exceptions import NotEnoughPermissionsException, ObjectNotFound, UserWithoutSessionException
from src.modules.tokens.dependencies import verify_access_token, verify_access_token_responses
from src.modules.users.repository import user_repository
from src.modules.users.schemas import ViewUser, view_from_user

router = APIRouter(prefix="/users", tags=["Users"])
docs.TAGS_INFO.append({"description": __doc__, "name": str(router.tags[0])})


UsersScopeDep = Annotated[JWTClaims, Security(verify_access_token, scopes=["users"])]


@router.get(
    "/me",
    responses={200: {"description": "Current user info"}, **UserWithoutSessionException.responses},
)
async def get_me(user_id: UserIdDep, request: Request) -> ViewUser:
    """
    Get current user info if authenticated
    """
    user = await user_repository.read(user_id)
    if user is None:
        # clear session cookie if user is not found
        request.session.clear()
        raise UserWithoutSessionException()
    return view_from_user(user)


SUGGEST_ON_TYPING_LIMIT = 10


@router.get(
    "/suggest-user-on-typing",
    responses={200: {"description": "Hint on type"}, **verify_access_token_responses},
)
async def get_hint_on_type(_: UserIdDep, query: str = Query(min_length=3)) -> list[ViewUser]:
    """
    Suggest user on typing, for example when invite to event.
    """
    users = await user_repository.search_by_query_with_rerank(query, limit=SUGGEST_ON_TYPING_LIMIT)

    return [view_from_user(u, include_update_data=False, include_deprecated_fields=False) for u in users]


def allowed_user_id_for_jwt_claims(
    user_id: PydanticObjectId | list[PydanticObjectId] | None, jwt_claims: JWTClaims
) -> bool:
    scope_string = jwt_claims.get("scope", "")
    scopes = scope_string.split() if scope_string else []
    users_scopes = [scope for scope in scopes if scope.startswith("users")]
    if "users" in users_scopes:  # wildcard
        return True

    if user_id:
        if isinstance(user_id, PydanticObjectId):
            return f"users:{user_id}" in users_scopes
        elif isinstance(user_id, list):
            return all(f"users:{user_id_item}" in users_scopes for user_id_item in user_id)

    return False


@router.get(
    "/by-telegram-id/{telegram_id}",
    responses={200: {"description": "User info"}, **ObjectNotFound.responses, **verify_access_token_responses},
)
async def get_user_by_telegram_id(telegram_id: int, jwt_claims: UsersScopeDep) -> ViewUser:
    """
    Get user by telegram id
    """

    user = await user_repository.read_by_telegram_id(telegram_id)
    if user is None or not allowed_user_id_for_jwt_claims(user.id, jwt_claims):
        raise ObjectNotFound("User not found")

    return view_from_user(user)


@router.post(
    "/by-id/get-bulk",
    responses={
        200: {"description": "Mapping [user_id -> user or None]"},
        **ObjectNotFound.responses,
        **NotEnoughPermissionsException.responses,
        **verify_access_token_responses,
    },
)
async def get_bulk_users_by_id(
    jwt_claims: UsersScopeDep, user_ids: list[PydanticObjectId] = Body(min_items=1)
) -> dict[PydanticObjectId, ViewUser | None]:
    """
    Get user by id
    """
    if not allowed_user_id_for_jwt_claims(user_ids, jwt_claims):
        raise NotEnoughPermissionsException("Not enough permissions")

    users = await user_repository.read_bulk(user_ids)
    return {user_id: view_from_user(user) if user else None for user_id, user in users.items()}


@router.get(
    "/by-id/{user_id}",
    responses={
        200: {"description": "User info"},
        **ObjectNotFound.responses,
        **verify_access_token_responses,
    },
)
async def get_user_by_id(user_id: PydanticObjectId, jwt_claims: UsersScopeDep) -> ViewUser:
    """
    Get user by id
    """
    if not allowed_user_id_for_jwt_claims(user_id, jwt_claims):
        raise ObjectNotFound("User not found because of insufficient permissions")
    user = await user_repository.read(user_id)
    if user is None:
        raise ObjectNotFound("User not found")
    return view_from_user(user)


@router.post(
    "/by-innomail/get-bulk",
    responses={
        200: {"description": "Mapping [email -> user or None]"},
        **ObjectNotFound.responses,
        **NotEnoughPermissionsException.responses,
        **verify_access_token_responses,
    },
)
async def get_bulk_users_by_innomail(
    jwt_claims: UsersScopeDep, emails: list[str] = Body(min_length=1)
) -> dict[str, ViewUser | None]:
    """
    Get users by email
    """

    users = await user_repository.read_by_innomail_bulk(emails)
    user_ids = [user.id for user in users.values() if user is not None]
    if not allowed_user_id_for_jwt_claims(user_ids, jwt_claims):
        raise NotEnoughPermissionsException("Not enough permissions")
    return {
        email: view_from_user(
            user,
            include_update_data=False,
            include_deprecated_fields=False,
        )
        if user
        else None
        for email, user in users.items()
    }


@router.get(
    "/by-innomail/{email}",
    responses={
        200: {"description": "User info"},
        **ObjectNotFound.responses,
        **verify_access_token_responses,
    },
)
async def get_user_by_innomail(email: str, jwt_claims: UsersScopeDep) -> ViewUser:
    """
    Get user by email
    """
    user = await user_repository.read_by_innomail(email)
    if user is None or not allowed_user_id_for_jwt_claims(user.id, jwt_claims):
        raise ObjectNotFound("User not found")
    return view_from_user(user)
