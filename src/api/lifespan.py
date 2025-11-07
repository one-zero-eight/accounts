__all__ = ["lifespan"]

import asyncio
from contextlib import asynccontextmanager

from beanie import init_beanie
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import timeout
from pymongo.errors import ConnectionFailure

from src.config import settings
from src.logging_ import logger
from src.modules.telegram_update.telegram_update_job import update_telegram_info
from src.storages.mongo.models import document_models


async def daily_loop_update_telegram_info():
    """Daily loop update telegram info"""
    while True:
        try:
            await update_telegram_info()

            # Wait for 24 hours
            await asyncio.sleep(86400)  # 86400 seconds = 24 hours
        except asyncio.CancelledError:
            logger.info("Daily job cancelled")
            break
        except Exception as e:
            logger.error(f"Error in daily job: {e}")
            await asyncio.sleep(3600)  # Wait 1 hour before retrying on error


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

    # Start daily loop update telegram info
    daily_task = asyncio.create_task(daily_loop_update_telegram_info())

    yield

    # Application shutdown
    daily_task.cancel()
    try:
        await daily_task
    except asyncio.CancelledError:
        pass
    motor_client.close()
