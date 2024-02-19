__all__ = ["lifespan"]

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from src.api.dependencies import Shared
from src.config import settings
from src.modules.clients.repository import ClientRepository
from src.modules.providers.email.repository import EmailFlowRepository
from src.modules.providers.innopolis.refresher import TokenRefresher
from src.modules.resources.repository import ResourceRepository
from src.modules.smtp.repository import SMTPRepository
from src.modules.users.repository import UserRepository


async def setup_repositories():
    mongo_client = AsyncIOMotorClient(settings.mongo.uri.get_secret_value())
    Shared.register_provider(AsyncIOMotorClient, mongo_client)
    mongo_db = mongo_client.get_default_database()
    Shared.register_provider(AsyncIOMotorDatabase, mongo_db)
    user_repository = UserRepository(mongo_db)
    Shared.register_provider(UserRepository, user_repository)
    email_flow_repository = EmailFlowRepository(mongo_db)
    Shared.register_provider(EmailFlowRepository, email_flow_repository)
    client_repository = ClientRepository(mongo_db)
    await client_repository.__post_init__()
    Shared.register_provider(ClientRepository, client_repository)
    resource_repository = ResourceRepository(mongo_db)
    await resource_repository.__post_init__()
    Shared.register_provider(ResourceRepository, resource_repository)
    if settings.smtp:
        smtp_repository = SMTPRepository()
        Shared.register_provider(SMTPRepository, smtp_repository)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Application startup

    await setup_repositories()

    if settings.innopolis_sso:
        from src.modules.providers.innopolis.routes import oauth

        refresher = TokenRefresher(oauth.innopolis)
        # noinspection PyAsyncCall
        asyncio.create_task(refresher.run())

    yield

    # Application shutdown
    from src.api.dependencies import Shared

    Shared.f(AsyncIOMotorClient).close()
