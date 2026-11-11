"""
Session on a mirror host: a copy of this API on another domain, for users whose network cannot reach the main host.
The browser does not send the session cookie of the main host to the mirror, so the frontend gets a transfer token
(a JWT that expires in 1 minute) from the main host and exchanges it here for the mirror's own session cookie.
"""

from beanie import PydanticObjectId
from fastapi import APIRouter, Request
from pydantic import BaseModel

from src.api import docs
from src.api.dependencies import UserDep, is_impersonating
from src.api.session import MIRROR_SESSION_KEY
from src.exceptions import InvalidTransferToken, NotEnoughPermissionsException, UserWithoutSessionException
from src.modules.tokens.repository import TokenRepository
from src.modules.users.repository import user_repository

router = APIRouter(prefix="/session/mirror", tags=["Session"])
docs.TAGS_INFO.append({"description": __doc__, "name": str(router.tags[0])})


class TransferTokenData(BaseModel):
    transfer_token: str


@router.post(
    "/transfer-token",
    responses={
        200: {"description": "Transfer token, valid for 1 minute"},
        **UserWithoutSessionException.responses,
        **NotEnoughPermissionsException.responses,
    },
)
async def create_transfer_token(user: UserDep, request: Request) -> TransferTokenData:
    """
    Create a short-lived token to set the session of the current user on the mirror host via `POST /session/mirror`.
    Expires in 1 minute. Not available while impersonating.
    """
    if is_impersonating(request):
        raise NotEnoughPermissionsException("Not available while impersonating")
    return TransferTokenData(transfer_token=TokenRepository.create_mirror_transfer_token(user))


@router.post(
    "",
    responses={204: {"description": "Mirror session is set"}, **InvalidTransferToken.responses},
    status_code=204,
)
async def set_mirror_session(data: TransferTokenData, request: Request):
    """
    Exchange a transfer token for the session cookie. Call it through the mirror host.
    A session of the main host is kept untouched.
    """
    uid = TokenRepository.verify_mirror_transfer_token(data.transfer_token)
    if uid is None or not await user_repository.exists(PydanticObjectId(uid)):
        raise InvalidTransferToken()

    if request.session.get("uid") and not request.session.get(MIRROR_SESSION_KEY):
        return None

    # The session may belong to another user who signed in here earlier
    request.session.clear()
    request.session["uid"] = uid
    request.session[MIRROR_SESSION_KEY] = True
    return None


@router.delete(
    "",
    responses={204: {"description": "Mirror session is cleared"}},
    status_code=204,
)
async def clear_mirror_session(request: Request):
    """
    Clear the session cookie of the mirror host, on sign out. A session of the main host is kept untouched.
    """
    if request.session.get(MIRROR_SESSION_KEY):
        request.session.clear()
    return None
