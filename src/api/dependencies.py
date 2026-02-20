__all__ = ["UserIdDep", "OptionalUserIdDep", "UserDep", "AdminDep", "impersonate_cookie_name"]

from typing import Annotated

from beanie import PydanticObjectId
from fastapi import Depends, Request

from src.config import settings
from src.config_schema import Environment
from src.exceptions import NotEnoughPermissionsException, UserWithoutSessionException
from src.modules.users.repository import user_repository
from src.storages.mongo.models import User

impersonate_cookie_name = (
    "__Secure-accounts-impersonate" if settings.environment == Environment.PRODUCTION else "accounts-impersonate"
)


async def _get_uid_from_session(request: Request) -> PydanticObjectId:
    uid = await _get_optional_uid_from_session(request)
    if uid is None:
        raise UserWithoutSessionException()
    return uid


async def _get_optional_uid_from_session(request: Request) -> PydanticObjectId | None:
    impersonate_uid = request.cookies.get(impersonate_cookie_name)
    if impersonate_uid:
        try:
            uid = PydanticObjectId(impersonate_uid)
            if await user_repository.exists(uid):
                return uid
        except Exception:
            pass

    uid = request.session.get("uid")
    if uid is None:
        return None
    uid = PydanticObjectId(uid)
    exists = await user_repository.exists(uid)
    if not exists:
        request.session.clear()
        raise UserWithoutSessionException()

    return uid


async def _get_user(request: Request) -> User:
    user_id = await _get_uid_from_session(request)
    user = await user_repository.read(user_id)
    if user is None:
        raise UserWithoutSessionException()
    return user


async def _get_admin_dep(user: User = Depends(_get_user)) -> User:
    if not user.is_admin:
        raise NotEnoughPermissionsException("You are not an admin")
    return user


UserIdDep = Annotated[PydanticObjectId, Depends(_get_uid_from_session)]
OptionalUserIdDep = Annotated[PydanticObjectId | None, Depends(_get_optional_uid_from_session, use_cache=False)]
UserDep = Annotated[User, Depends(_get_user)]
AdminDep = Annotated[User, Depends(_get_admin_dep)]
