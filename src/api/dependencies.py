__all__ = ["Shared", "UserIdDep", "OptionalUserIdDep", "UserDep", "VerifiedClientIdDep"]

from typing import Callable, TypeVar, Union, ClassVar, Hashable, Annotated
from fastapi import Request, Depends

from src.exceptions import UserWithoutSessionException
from src.modules.users.repository import MongoUser, UserRepository
from src.mongo_object_id import PyObjectId

T = TypeVar("T")

CallableOrValue = Union[Callable[[], T], T]


class Shared:
    """
    Key-value storage with generic type support for accessing shared dependencies
    """

    __slots__ = ()

    providers: ClassVar[dict[type, CallableOrValue]] = {}

    @classmethod
    def register_provider(cls, key: type[T] | Hashable, provider: CallableOrValue):
        cls.providers[key] = provider

    @classmethod
    def f(cls, key: type[T] | Hashable) -> T:
        """
        Get shared dependency by key (f - fetch)
        """
        if key not in cls.providers:
            if isinstance(key, type):
                # try by classname
                key = key.__name__

                if key not in cls.providers:
                    raise KeyError(f"Provider for {key} is not registered")

            elif isinstance(key, str):
                # try by classname
                for cls_key in cls.providers.keys():
                    if cls_key.__name__ == key:
                        key = cls_key
                        break
                else:
                    raise KeyError(f"Provider for {key} is not registered")

        provider = cls.providers[key]

        if callable(provider):
            return provider()
        else:
            return provider


async def _get_uid_from_session(request: Request) -> PyObjectId:
    uid = await _get_optional_uid_from_session(request)
    if uid is None:
        raise UserWithoutSessionException()
    return uid


async def _get_optional_uid_from_session(request: Request) -> PyObjectId | None:
    uid = request.session.get("uid")

    if uid is None:
        return None
    uid = PyObjectId(uid)
    exists = await Shared.f(UserRepository).exists(uid)
    if not exists:
        request.session.clear()
        raise UserWithoutSessionException()

    return uid


async def _get_user(request: Request) -> MongoUser:
    user_id = await _get_uid_from_session(request)
    user_repository = Shared.f(UserRepository)
    user = await user_repository.read(user_id)
    return user


UserIdDep = Annotated[PyObjectId, Depends(_get_uid_from_session)]
OptionalUserIdDep = Annotated[PyObjectId | None, Depends(_get_optional_uid_from_session, use_cache=False)]
UserDep = Annotated[MongoUser, Depends(_get_user)]

from src.modules.clients.dependencies import VerifiedClientIdDep  # noqa: E402
