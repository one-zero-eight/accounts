__all__ = ["ClienRepository"]

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.clients.abc import AbstractClientRepository
from src.schemas.clients import CreateOauth2Client, ViewOauth2Client
from src.storages.sql import AbstractSQLAlchemyStorage
from src.storages.sql.models import Oauth2Client


class ClienRepository(AbstractClientRepository):
    storage: AbstractSQLAlchemyStorage

    def __init__(self, storage: AbstractSQLAlchemyStorage):
        self.storage = storage

    def _create_session(self) -> AsyncSession:
        return self.storage.create_session()

    # ----------------- CRUD ----------------- #
    async def create_client(self, client: CreateOauth2Client) -> ViewOauth2Client:
        async with self._create_session() as session:
            q = insert(Oauth2Client).values(**client.model_dump())
            await session.execute(q)
            await session.commit()
            return ViewOauth2Client(**client.model_dump())

    async def read_client(self, client_id: str) -> ViewOauth2Client:
        async with self._create_session() as session:
            q = select(Oauth2Client).where(Oauth2Client.client_id == client_id)
            client = await session.scalar(q)
            return ViewOauth2Client.model_validate(client)
