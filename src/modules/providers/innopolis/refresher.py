import asyncio
import datetime

from authlib.integrations.httpx_client import AsyncOAuth2Client
from authlib.integrations.starlette_client import StarletteOAuth2App
from authlib.oauth2.rfc6749 import OAuth2Token

from src.api.dependencies import Shared
from src.logging_ import logger
from src.modules.providers.innopolis.schemas import UserInfoFromSSO
from src.modules.users.repository import UserRepository, MongoUser

from asyncio import TaskGroup, Semaphore

from src.mongo_object_id import PyObjectId


# noinspection PyMethodMayBeStatic
class TokenRefresher:
    def __init__(
        self,
        _oauth: StarletteOAuth2App,
        every: datetime.timedelta = datetime.timedelta(minutes=5),
        die_in: datetime.timedelta = datetime.timedelta(minutes=10),
    ):
        logger.info(f"Token refresher started with {every=} {die_in=}")
        self.every = every
        self.die_in = die_in
        self._oauth = _oauth

    async def refresh_token_method(self, refresh_token: str) -> OAuth2Token:
        metadata = await self._oauth.load_server_metadata()
        async with self._oauth._get_oauth_client(**metadata) as client:  # noqa
            client: AsyncOAuth2Client
            refreshed_token = await client.refresh_token(metadata.get("token_endpoint"), refresh_token=refresh_token)
        return refreshed_token

    async def update_user(self, user_id: PyObjectId, token: OAuth2Token):
        users_repository = Shared.f(UserRepository)
        if "id_token" in token:
            userinfo = await self._oauth.parse_id_token(token, nonce=None)
            token["userinfo"] = userinfo
        user_info = UserInfoFromSSO.from_token_and_userinfo(token, token["userinfo"])

        await users_repository.update_innopolis_sso(user_id, user_info)

    async def _task(self, user: MongoUser):
        logger.info(f"Refreshing token for {user.object_id=}")
        refreshed_token = await self.refresh_token_method(user.innopolis_sso.refresh_token)
        if refreshed_token:
            await self.update_user(user.object_id, refreshed_token)

    async def __call__(self):
        users_repository = Shared.f(UserRepository)
        users = await users_repository.get_all_users_with_old_innopolis_sso(self.die_in)
        sem = Semaphore(16)
        async with sem:
            async with TaskGroup() as tg:
                for user in users:
                    await tg.create_task(self._task(user))

    async def run(self):
        while True:
            await self()
            await asyncio.sleep(self.every.total_seconds())
