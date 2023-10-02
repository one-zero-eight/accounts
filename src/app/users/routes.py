from src.app.dependencies import (
    USER_REPOSITORY_DEPENDENCY,
    CURRENT_USER_ID_DEPENDENCY,
)
from src.app.users import router
from src.exceptions import (
    IncorrectCredentialsException,
    NoCredentialsException,
)
from src.schemas import ViewUser


@router.get(
    "/me",
    responses={
        200: {"description": "Current user info"},
        **IncorrectCredentialsException.responses,
        **NoCredentialsException.responses,
    },
)
async def get_me(
    user_id: CURRENT_USER_ID_DEPENDENCY,
    user_repository: USER_REPOSITORY_DEPENDENCY,
) -> ViewUser:
    """
    Get current user info if authenticated
    """
    user = await user_repository.read(user_id)
    user: ViewUser
    return user
