__all__ = ["AbstractUserRepository"]

from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from src.schemas.users import UserInfoFromSSO
    from src.schemas import ViewUser


class AbstractUserRepository(metaclass=ABCMeta):
    # ----------------- CRUD ----------------- #
    @abstractmethod
    async def register_or_update_via_innopolis_sso(self, user_info: "UserInfoFromSSO") -> "ViewUser":
        ...

    @abstractmethod
    async def read(self, id_: int) -> "ViewUser":
        ...

    @abstractmethod
    async def read_by_innopolis_email(self, innopolis_email: str) -> "ViewUser":
        ...
