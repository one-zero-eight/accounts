from beanie import PydanticObjectId, UpdateResponse
from beanie.odm.operators.find.comparison import In
from beanie.odm.operators.update.general import Set

from src.modules.providers.innopolis.schemas import UserInfoFromSSO
from src.modules.providers.telegram.schemas import TelegramWidgetData
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
        user = await User.find_one(User.id == user_id).update(Set({User.telegram: telegram_data}))
        return user

    async def exists(self, user_id: PydanticObjectId) -> bool:
        exists = bool(await User.find(User.id == user_id, limit=1).count())
        return exists

    async def read(self, user_id: PydanticObjectId) -> User | None:
        user = await User.find_one(User.id == user_id)
        return user

    async def read_bulk(self, user_ids: list[PydanticObjectId]) -> dict[PydanticObjectId, User | None]:
        result = dict.fromkeys(user_ids, None)
        users = await User.find(In(User.id, user_ids)).to_list()
        for user in users:
            result[user.id] = user
        return result

    async def read_by_telegram_id(self, telegram_id: int) -> User | None:
        user = await User.find_one(User.telegram.id == telegram_id)
        return user

    async def read_by_innomail(self, email: str) -> User | None:
        user = await User.find_one(User.innopolis_sso.email == email)
        return user

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


user_repository: UserRepository = UserRepository()
