from fastapi import HTTPException
from starlette import status


class UserWithoutSessionException(HTTPException):
    """
    HTTP_401_UNAUTHORIZED
    """

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=self.responses[401]["description"],
        )

    responses = {401: {"description": "User does not have a session cookie or `uid` in the session"}}


class IncorrectCredentialsException(HTTPException):
    """
    HTTP_401_UNAUTHORIZED
    """

    def __init__(self, no_credentials: bool = False) -> None:
        if no_credentials:
            super().__init__(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No credentials provided",
                headers={"WWW-Authenticate": "Bearer"},
            )
        else:
            super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

    responses = {401: {"description": "Could not validate credentials: token is invalid OR no credentials provided"}}


class ClientIncorrectCredentialsException(HTTPException):
    """
    HTTP_401_UNAUTHORIZED
    """

    def __init__(self, no_credentials: bool = False) -> None:
        if no_credentials:
            super().__init__(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No credentials provided",
                headers={"WWW-Authenticate": "Bearer"},
            )
        else:
            super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

    responses = {401: {"description": "Could not validate credentials: token is invalid OR no credentials provided"}}


class NotEnoughPermissionsException(HTTPException):
    """
    HTTP_403_FORBIDDEN
    """

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=self.responses[403]["description"],
        )

    responses = {403: {"description": "Not enough permissions"}}


class InvalidReturnToURL(HTTPException):
    """
    HTTP_400_BAD_REQUEST
    """

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=self.responses[400]["description"],
        )

    responses = {400: {"description": "Invalid redirect_uri URL"}}


class InvalidTelegramWidgetHash(HTTPException):
    """
    HTTP_400_BAD_REQUEST
    """

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=self.responses[400]["description"],
        )

    responses = {400: {"description": "Invalid Telegram widget hash"}}
