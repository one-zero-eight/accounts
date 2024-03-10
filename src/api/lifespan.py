__all__ = ["lifespan"]

import json
from contextlib import asynccontextmanager

from beanie import init_beanie
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import timeout
from pymongo.errors import ConnectionFailure

from src.config import settings
from src.logging_ import logger
from src.storages.mongo.models import document_models


async def setup_repositories() -> AsyncIOMotorClient:
    motor_client = AsyncIOMotorClient(
        settings.mongo.uri.get_secret_value(), connectTimeoutMS=5000, serverSelectionTimeoutMS=5000
    )

    # healthcheck mongo
    try:
        with timeout(1):
            server_info = await motor_client.server_info()
            server_info_pretty_text = json.dumps(server_info, indent=2, default=str)
            logger.info(f"Connected to MongoDB: {server_info_pretty_text}")
    except ConnectionFailure as e:
        logger.critical("Could not connect to MongoDB: %s" % e)

    mongo_db = motor_client.get_default_database()
    await init_beanie(database=mongo_db, document_models=document_models)
    return motor_client


async def setup_predefined() -> None:
    from src.modules.resources.repository import resource_repository

    for resource in settings.predefined.resources:
        if not await resource_repository.read(resource.resource_id):
            logger.info(f"Creating predefined resource {resource=}")
            await resource_repository.create(resource)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Application startup

    motor_client = await setup_repositories()
    await setup_predefined()

    yield

    # Application shutdown
    motor_client.close()
