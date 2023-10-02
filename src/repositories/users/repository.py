__all__ = ["UserRepository"]

import random
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import exists

from src.exceptions import DBUserAlreadyExists
from src.repositories.users.abc import AbstractUserRepository
from src.schemas.users import ViewUser, UserInfoFromSSO
from src.storages.sql.models import User, InnopolisSSOUser
from src.storages.sql.storage import AbstractSQLAlchemyStorage


MIN_USER_ID = 100_000
MAX_USER_ID = 999_999


async def _get_available_user_ids(
    session: AsyncSession, count: int = 1
) -> list[int] | int:
    q = select(User.id)
    excluded_ids = set(await session.scalars(q))
    excluded_ids: set[int]
    available_ids = set()
    while len(available_ids) < count:
        chosen_id = random.randint(MIN_USER_ID, MAX_USER_ID)
        if chosen_id not in excluded_ids:
            available_ids.add(chosen_id)
    return list(available_ids) if count > 1 else available_ids.pop()


class UserRepository(AbstractUserRepository):
    storage: AbstractSQLAlchemyStorage

    def __init__(self, storage: AbstractSQLAlchemyStorage):
        self.storage = storage

    def _create_session(self) -> AsyncSession:
        return self.storage.create_session()

    # ------------------ CRUD ------------------ #
    async def register_or_update_via_innopolis_sso(
        self, user_info: UserInfoFromSSO
    ) -> ViewUser:
        async with self._create_session() as session:
            # Check if user already exists
            q = select(exists().where(InnopolisSSOUser.email == user_info.email))

            if await session.scalar(q):
                # update InnopolisSSOUser
                q = (
                    update(InnopolisSSOUser)
                    .where(InnopolisSSOUser.email == user_info.email)
                    .values(
                        status=user_info.status,
                        name=user_info.name,
                    )
                )
                await session.execute(q)
                await session.commit()

                # return existing user
                q = (
                    select(User)
                    .where(InnopolisSSOUser.email == user_info.email)
                )
                user = await session.scalar(q)
                return ViewUser.model_validate(user, from_attributes=True)

            # Get available user id
            user_id = await _get_available_user_ids(session)

            # Create user
            user = User(
                id=user_id,
                innopolis_sso=InnopolisSSOUser(
                    id=user_id, **user_info.model_dump(exclude_none=True)
                ),
            )
            session.add(user)
            await session.commit()
            return ViewUser.model_validate(user, from_attributes=True)

    async def read(self, id_: int) -> Optional["ViewUser"]:
        async with self._create_session() as session:
            q = (
                select(User)
                .where(User.id == id_)
            )
            user = await session.scalar(q)
            if user:
                return ViewUser.model_validate(user, from_attributes=True)

    async def read_by_innopolis_email(
        self, innopolis_email: str
    ) -> Optional["ViewUser"]:
        async with self._create_session() as session:
            q = (
                select(User)
                .where(InnopolisSSOUser.email == innopolis_email)
            )
            user = await session.scalar(q)
            if user:
                return ViewUser.model_validate(user, from_attributes=True)

    # ^^^^^^^^^^^^^^^^^^^ CRUD ^^^^^^^^^^^^^^^^^^^ #
