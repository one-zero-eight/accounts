import re

from beanie import PydanticObjectId, UpdateResponse
from beanie.odm.operators.find.comparison import In
from beanie.odm.operators.update.general import Set

from src.modules.providers.innopolis.schemas import UserInfoFromSSO
from src.modules.providers.telegram.schemas import TelegramWidgetData
from src.modules.users.schemas import BulkExportUser
from src.modules.users.search import norm, norm_tg, rank_users
from src.storages.mongo.models import User


# noinspection PyMethodMayBeStatic
class UserRepository:
    async def register_or_update_via_innopolis_sso(self, user_info: UserInfoFromSSO) -> User:
        # check if user exists
        user = await User.find_one(User.innopolis_sso.email == user_info.email).upsert(
            Set({User.innopolis_sso: user_info}),
            on_insert=User(innopolis_sso=user_info),
            response_type=UpdateResponse.NEW_DOCUMENT,
        )

        return user

    async def update_innopolis_sso(self, user_id: PydanticObjectId, user_info: UserInfoFromSSO) -> User:
        user = await User.find_one(User.id == user_id).update(Set({User.innopolis_sso: user_info}))
        return user

    async def update_telegram(self, user_id: PydanticObjectId, telegram_data: TelegramWidgetData) -> User:
        user = await User.find_one(User.id == user_id).update(
            Set({User.telegram: telegram_data, User.telegram_update_data: None})
        )
        return user

    async def exists(self, user_id: PydanticObjectId) -> bool:
        exists = bool(await User.find(User.id == user_id, limit=1).count())
        return exists

    async def read(self, user_id: PydanticObjectId) -> User | None:
        user = await User.find_one(User.id == user_id)
        return user

    async def update_preferences(self, user_id: PydanticObjectId, preferences: dict[str, int | None]) -> User | None:
        if not preferences:
            return await self.read(user_id)

        update: dict[str, dict[str, int | str]] = {}
        for field, value in preferences.items():
            path = f"preferences.{field}"
            if value is None:
                update.setdefault("$unset", {})[path] = ""
            else:
                update.setdefault("$set", {})[path] = value

        collection = User.get_motor_collection()
        result = await collection.update_one({"_id": user_id}, update)
        if result.matched_count == 0:
            return None

        await collection.update_one({"_id": user_id, "preferences": {}}, {"$unset": {"preferences": ""}})
        return await self.read(user_id)

    async def read_bulk(self, user_ids: list[PydanticObjectId]) -> dict[PydanticObjectId, User | None]:
        result = dict.fromkeys(user_ids, None)
        users = await User.find(In(User.id, user_ids)).to_list()
        for user in users:
            result[user.id] = user
        return result

    async def read_all_users_with_telegram_id(self) -> dict[PydanticObjectId, int]:
        result = dict()
        users = (
            await User.get_motor_collection()
            .aggregate(
                [
                    {
                        "$match": {
                            "telegram.id": {
                                "$exists": True,
                            },
                        },
                    },
                    {
                        "$project": {
                            "_id": 1,
                            "telegram.id": 1,
                        },
                    },
                ]
            )
            .to_list()
        )
        for user in users:
            result[user["_id"]] = user["telegram"]["id"]
        return result

    async def read_all_for_my_uni_export(self) -> list[BulkExportUser]:
        users = (
            await User.get_motor_collection()
            .aggregate(
                [
                    {"$sort": {"_id": 1}},
                    {
                        "$project": {
                            "_id": 0,
                            "email": {"$ifNull": ["$innopolis_sso.email", None]},
                            "telegram_id": {"$ifNull": ["$telegram.id", None]},
                            "telegram_alias": {
                                "$cond": [
                                    {"$eq": ["$telegram_update_data.success", True]},
                                    {"$ifNull": ["$telegram_update_data.username", None]},
                                    {"$ifNull": ["$telegram.username", None]},
                                ],
                            },
                        },
                    },
                ]
            )
            .to_list()
        )
        return [BulkExportUser.model_validate(user) for user in users]

    async def read_by_telegram_id(self, telegram_id: int) -> User | None:
        user = await User.find_one(User.telegram.id == telegram_id)
        return user

    async def read_by_innomail(self, email: str) -> User | None:
        user = await User.find_one(User.innopolis_sso.email == email)
        return user

    async def read_by_innomail_bulk(self, emails: list[str]) -> dict[str, User | None]:
        result = dict.fromkeys(emails, None)
        users = await User.find(In(User.innopolis_sso.email, emails)).to_list()
        for user in users:
            result[user.innopolis_sso.email] = user
        return result

    async def wild_read(
        self, user_id: PydanticObjectId | None, telegram_id: int | None, email: str | None
    ) -> User | None:
        predicates = []
        if user_id is not None:
            predicates.append(User.id == user_id)
        if telegram_id is not None:
            predicates.append(User.telegram.id == telegram_id)
        if email is not None:
            predicates.append(User.innopolis_sso.email == email)
        user = await User.find_one(*predicates)
        return user

    async def search_by_query_with_rerank(self, query: str, limit: int = 10) -> list[User]:
        norm_tg_query = norm_tg(norm(query))
        pattern = re.escape(norm_tg_query)
        prefetch_users = await User.find(
            {
                "$or": [
                    {User.innopolis_sso.email: {"$regex": pattern, "$options": "i"}},
                    {User.telegram.username: {"$regex": pattern, "$options": "i"}},
                    {User.innopolis_sso.name: {"$regex": pattern, "$options": "i"}},
                ]
            }
        ).to_list()

        scored = rank_users(prefetch_users, query, limit=limit)
        return [r.user for r in scored]


user_repository: UserRepository = UserRepository()
