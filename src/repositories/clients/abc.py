__all__ = ["AbstractClientRepository"]

from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from src.schemas.clients import ViewOauth2Client, CreateOauth2Client


class AbstractClientRepository(metaclass=ABCMeta):
    @abstractmethod
    async def read_client(self, client_id: str) -> ViewOauth2Client:
        ...

    @abstractmethod
    async def create_client(self, client: CreateOauth2Client) -> ViewOauth2Client:
        ...
