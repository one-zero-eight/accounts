__all__ = ["VerifiedClientIdDep", "security"]

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from src.api.dependencies import Shared
from src.exceptions import ClientIncorrectCredentialsException
from src.modules.clients.repository import ClientRepository, VerificationResultStatus

security = HTTPBasic(auto_error=False)


async def _get_client_id(credentials: Annotated[HTTPBasicCredentials | None, Depends(security)]) -> str:
    if credentials is None:
        raise ClientIncorrectCredentialsException(no_credentials=True)

    client_repository = Shared.f(ClientRepository)
    verification = await client_repository.verify(credentials.username, credentials.password)
    if verification.status == VerificationResultStatus.SUCCESS:
        return verification.client_id
    else:
        raise ClientIncorrectCredentialsException()


VerifiedClientIdDep = Annotated[str, Depends(_get_client_id)]
