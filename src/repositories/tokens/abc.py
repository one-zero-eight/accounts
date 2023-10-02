__all__ = ["AbstractTokenRepository"]

from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING

from src.schemas.oauth2 import UserTokenData

if TYPE_CHECKING:
    ...


class AbstractTokenRepository(metaclass=ABCMeta):
    @abstractmethod
    async def verify_user_token(self, token: str) -> UserTokenData:
        ...

    @abstractmethod
    def create_access_token(self, user_id: int) -> str:
        ...
