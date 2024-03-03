__all__ = ["VerifiedClientIdDep", "basic", "ClientRegistrationAccessTokenDep", "bearer"]

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials, HTTPBearer, HTTPAuthorizationCredentials

from src.exceptions import ClientIncorrectCredentialsException
from src.modules.clients.schemas import VerificationResultStatus

basic = HTTPBasic(auto_error=False)


async def _get_client_id(credentials: Annotated[HTTPBasicCredentials | None, Depends(basic)]) -> str:
    from src.modules.clients.repository import client_repository

    if credentials is None:
        raise ClientIncorrectCredentialsException(no_credentials=True)
    verification = await client_repository.verify(credentials.username, credentials.password)
    if verification.status == VerificationResultStatus.SUCCESS:
        return verification.client_id
    else:
        raise ClientIncorrectCredentialsException()


bearer = HTTPBearer(auto_error=False)


async def _get_client_registration_access_token(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> str | None:
    if credentials is None or not credentials.credentials.startswith("reg"):
        return None
    return credentials.credentials


VerifiedClientIdDep = Annotated[str, Depends(_get_client_id)]
ClientRegistrationAccessTokenDep = Annotated[str | None, Depends(_get_client_registration_access_token)]
