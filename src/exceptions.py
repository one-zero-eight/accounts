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


class NotEnoughPermissionsException(HTTPException):
    """
    HTTP_403_FORBIDDEN
    """

    def __init__(self, detail: str | None = None) -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail or self.responses[403]["description"],
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


class InvalidScope(HTTPException):
    """
    HTTP_400_BAD_REQUEST
    """

    def __init__(self, detail: str | None = None) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail or self.responses[400]["description"],
        )

    responses = {400: {"description": "Invalid scope"}}


class ObjectNotFound(HTTPException):
    """
    HTTP_404_NOT_FOUND
    """

    def __init__(self, detail: str = None):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail or self.responses[404]["description"],
        )

    responses = {404: {"description": "Object with such properties not found"}}
