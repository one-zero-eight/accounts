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
