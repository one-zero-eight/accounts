__all__ = [
    "STORAGE_DEPENDENCY",
    "USER_REPOSITORY_DEPENDENCY",
    "CURRENT_USER_ID_DEPENDENCY",
    "Dependencies",
]

from typing import Annotated, Callable

from fastapi import Depends

from src.repositories.clients import AbstractClientRepository
from src.repositories.users import AbstractUserRepository
from src.storages.sql.storage import AbstractSQLAlchemyStorage


class Dependencies:
    _storage: "AbstractSQLAlchemyStorage"
    _user_repository: "AbstractUserRepository"
    _client_repository: "AbstractClientRepository"

    @classmethod
    def get_storage(cls) -> "AbstractSQLAlchemyStorage":
        return cls._storage

    @classmethod
    def set_storage(cls, storage: "AbstractSQLAlchemyStorage"):
        cls._storage = storage

    @classmethod
    def get_user_repository(cls) -> "AbstractUserRepository":
        return cls._user_repository

    @classmethod
    def set_user_repository(cls, user_repository: "AbstractUserRepository"):
        cls._user_repository = user_repository

    @classmethod
    def get_client_repository(cls) -> "AbstractClientRepository":
        return cls._client_repository

    @classmethod
    def set_client_repository(cls, client_repository: "AbstractClientRepository"):
        cls._client_repository = client_repository

    get_current_user_id: Callable[..., str]


STORAGE_DEPENDENCY = Annotated[
    AbstractSQLAlchemyStorage, Depends(Dependencies.get_storage)
]
USER_REPOSITORY_DEPENDENCY = Annotated[
    AbstractUserRepository, Depends(Dependencies.get_user_repository)
]
CLIENT_REPOSITORY_DEPENDENCY = Annotated[
    AbstractClientRepository, Depends(Dependencies.get_client_repository)
]

from src.app.oauth.dependencies import get_current_user_id  # noqa: E402

Dependencies.get_current_user_id = get_current_user_id

CURRENT_USER_ID_DEPENDENCY = Annotated[str, Depends(Dependencies.get_current_user_id)]
