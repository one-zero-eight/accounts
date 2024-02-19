import datetime

from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field
from pymongo import ReturnDocument

from src.logging_ import logger
from src.modules.providers.innopolis.schemas import UserInfoFromSSO
from src.modules.providers.telegram.schemas import TelegramWidgetData
from src.mongo_object_id import PyObjectId
from src.utils import aware_utcnow


class User(BaseModel):
    innopolis_sso: UserInfoFromSSO | None = None
    telegram: TelegramWidgetData | None = None


class MongoUser(User):
    object_id: PyObjectId = Field(alias="_id")


class UserRepository:
    def __init__(self, database: AsyncIOMotorDatabase, *, collection: str = "users") -> None:
        self.__database = database
        self.__collection = database[collection]

    async def register_or_update_via_innopolis_sso(self, user_info: UserInfoFromSSO) -> MongoUser:
        # check if user exists
        user = await self.__collection.find_one_and_update(
            {"innopolis_sso.email": user_info.email},
            {"$set": {"innopolis_sso": user_info.model_dump()}},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        return MongoUser.model_validate(user)

    async def update_innopolis_sso(self, user_id: PyObjectId, user_info: UserInfoFromSSO) -> MongoUser:
        logger.debug(f"Updating user {user_id}:\n{user_info.model_dump_json(indent=2)}")
        user = await self.__collection.find_one_and_update(
            {"_id": user_id},
            {"$set": {"innopolis_sso": user_info.model_dump()}},
            return_document=ReturnDocument.AFTER,
        )
        return MongoUser.model_validate(user)

    async def update_telegram(self, user_id: PyObjectId, telegram_data: TelegramWidgetData) -> MongoUser:
        user = await self.__collection.find_one_and_update(
            {"_id": user_id},
            {"$set": {"telegram": telegram_data.model_dump()}},
            return_document=ReturnDocument.AFTER,
        )
        return MongoUser.model_validate(user)

    async def exists(self, user_id: PyObjectId) -> bool:
        return await self.__collection.count_documents({"_id": user_id}, limit=1) > 0

    async def read(self, user_id: PyObjectId) -> MongoUser | None:
        user = await self.__collection.find_one({"_id": user_id})
        if user:
            return MongoUser.model_validate(user)

    async def read_by_telegram_id(self, telegram_id: int) -> MongoUser | None:
        user = await self.__collection.find_one({"telegram.id": telegram_id})
        if user:
            return MongoUser.model_validate(user)

    async def get_all_users_with_old_innopolis_sso(self, die_in: datetime.timedelta) -> list[MongoUser]:
        users = self.__collection.find({"innopolis_sso.expires_at": {"$lt": aware_utcnow() + die_in}})
        return [MongoUser.model_validate(user) async for user in users]
