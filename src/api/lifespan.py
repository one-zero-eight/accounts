__all__ = ["lifespan"]

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
            vesion = server_info["version"]
            logger.info(f"Connected to MongoDB v{vesion}")
    except ConnectionFailure as e:
        logger.critical(f"Could not connect to MongoDB: {e}")

    mongo_db = motor_client.get_default_database()
    await init_beanie(database=mongo_db, document_models=document_models)
    return motor_client


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Application startup

    motor_client = await setup_repositories()

    yield

    # Application shutdown
    motor_client.close()
