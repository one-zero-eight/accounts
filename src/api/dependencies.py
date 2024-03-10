__all__ = ["UserIdDep", "OptionalUserIdDep", "UserDep", "AdminDep"]

from typing import Annotated
from fastapi import Request, Depends

from src.exceptions import UserWithoutSessionException, NotEnoughPermissionsException
from src.modules.users.repository import user_repository
from src.storages.mongo.models import User
from beanie import PydanticObjectId


async def _get_uid_from_session(request: Request) -> PydanticObjectId:
    uid = await _get_optional_uid_from_session(request)
    if uid is None:
        raise UserWithoutSessionException()
    return uid


async def _get_optional_uid_from_session(request: Request) -> PydanticObjectId | None:
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
    return user


async def _get_admin_dep(user: User = Depends(_get_user)) -> User:
    if not user.is_admin:
        raise NotEnoughPermissionsException("You are not an admin")
    return user


UserIdDep = Annotated[PydanticObjectId, Depends(_get_uid_from_session)]
OptionalUserIdDep = Annotated[PydanticObjectId | None, Depends(_get_optional_uid_from_session, use_cache=False)]
UserDep = Annotated[User, Depends(_get_user)]
AdminDep = Annotated[User, Depends(_get_admin_dep)]
