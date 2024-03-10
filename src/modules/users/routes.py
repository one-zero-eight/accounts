from fastapi import APIRouter, Request

from src.api.dependencies import UserIdDep
from src.exceptions import UserWithoutSessionException
from src.modules.users.repository import user_repository
from src.storages.mongo.models import User

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/me",
    responses={200: {"description": "Current user info"}, **UserWithoutSessionException.responses},
)
async def get_me(user_id: UserIdDep, request: Request) -> User:
    """
    Get current user info if authenticated
    """
    user = await user_repository.read(user_id)
    if user is None:
        # clear session cookie if user is not found
        request.session.clear()
        raise UserWithoutSessionException()
    return user


#
# @router.get(
#     "/by-telegram-id/{telegram_id}",
#     response_model=User,
#     responses={200: {"description": "User info"}, **ObjectNotFound.responses},
# )
# async def get_user_by_telegram_id(telegram_id: int) -> User:
#     """
#     Get user by telegram id
#     """
#     user = await user_repository.read_by_telegram_id(telegram_id)
#     if user is None:
#         raise ObjectNotFound("User not found")
#
#     return user
#
#
# @router.get(
#     "/by-id/{user_id}",
#     response_model=User,
#     responses={200: {"description": "User info"}, **ObjectNotFound.responses},
# )
# async def get_user_by_id(user_id: PydanticObjectId) -> User:
#     """
#     Get user by id
#     """
#     user = await user_repository.read(user_id)
#     if user is None:
#         raise ObjectNotFound("User not found")
#
#     return user
#
#
# @router.get(
#     "/by-innomail/{email}",
#     response_model=User,
#     responses={200: {"description": "User info"}, **ObjectNotFound.responses},
# )
# async def get_user_by_innomail(email: str) -> User:
#     """
#     Get user by email
#     """
#     user = await user_repository.read_by_innomail(email)
#     if user is None:
#         raise ObjectNotFound("User not found")
#
#     return user
