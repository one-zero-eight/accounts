__all__ = []

import warnings
from typing import Optional, Annotated

from fastapi import Depends

from src.app.dependencies import Dependencies
from src.app.oauth import router
from src.repositories.tokens import TokenRepository
from src.app.oauth.redirect import (
    redirect_with_token_as_cookie,
    ensure_allowed_redirect_uri,
)
from src.config import settings, Environment
from src.repositories.users import AbstractUserRepository

enabled = (
    bool(settings.DEV_AUTH_EMAIL) and settings.ENVIRONMENT == Environment.DEVELOPMENT
)

if enabled:
    from src.schemas.users import UserInfoFromSSO

    warnings.warn(
        "Dev auth provider is enabled! "
        "Use this only for development environment "
        "(otherwise, set ENVIRONMENT=production)."
    )

    @router.get("/dev/login")
    async def dev_login(
        user_repository: Annotated[
            AbstractUserRepository, Depends(Dependencies.get_user_repository)
        ],
        redirect_uri: str = "/",
        email: Optional[str] = None,
    ):
        ensure_allowed_redirect_uri(redirect_uri)
        email = email or settings.DEV_AUTH_EMAIL
        user = await user_repository.register_or_update_via_innopolis_sso(
            UserInfoFromSSO(email=email, status="student", name="Dev User")
        )
        token = TokenRepository.create_access_token(user.id)
        return redirect_with_token_as_cookie(redirect_uri, token)

    @router.get("/dev/token")
    async def get_dev_token(
        user_repository: Annotated[
            AbstractUserRepository, Depends(Dependencies.get_user_repository)
        ],
        email: Optional[str] = None,
    ) -> str:
        email = email or settings.DEV_AUTH_EMAIL
        user = await user_repository.register_or_update_via_innopolis_sso(
            UserInfoFromSSO(email=email, status="student", name="Dev User")
        )
        return TokenRepository.create_access_token(user.id)
