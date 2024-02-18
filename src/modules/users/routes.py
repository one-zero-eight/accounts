from fastapi import APIRouter, Request

from src.api.dependencies import Shared, UserIdDep
from src.exceptions import UserWithoutSessionException
from src.modules.users.repository import UserRepository, MongoUser

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/me",
    responses={200: {"description": "Current user info"}, **UserWithoutSessionException.responses},
)
async def get_me(user_id: UserIdDep, request: Request) -> MongoUser:
    """
    Get current user info if authenticated
    """
    user = await Shared.f(UserRepository).read(user_id)
    if user is None:
        # clear session cookie if user is not found
        request.session.clear()
        raise UserWithoutSessionException()
    return user
