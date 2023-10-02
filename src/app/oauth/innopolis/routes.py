__all__ = []

from typing import Annotated

from authlib.integrations.base_client import MismatchingStateError
from fastapi import Depends
from starlette.requests import Request
from starlette.responses import RedirectResponse, JSONResponse

from src import constants
from src.app.dependencies import Dependencies
from src.app.oauth import oauth
from src.app.oauth.dependencies import get_current_user_id
from src.app.oauth.innopolis import router
from src.repositories.tokens import TokenRepository
from src.app.oauth.redirect import (
    redirect_with_token_as_cookie,
    ensure_allowed_redirect_uri,
)
from src.config import settings
from src.exceptions import NoCredentialsException, IncorrectCredentialsException
from src.repositories.users.abc import AbstractUserRepository
from src.schemas.users import UserInfoFromSSO

enabled = bool(settings.INNOPOLIS_SSO_CLIENT_ID.get_secret_value())

if enabled:
    redirect_uri = settings.INNOPOLIS_SSO_REDIRECT_URI

    innopolis_sso = oauth.register(
        "innopolis",
        client_id=settings.INNOPOLIS_SSO_CLIENT_ID.get_secret_value(),
        client_secret=settings.INNOPOLIS_SSO_CLIENT_SECRET.get_secret_value(),
        # OAuth client will fetch configuration on first request
        server_metadata_url="https://sso.university.innopolis.ru/adfs/.well-known/openid-configuration",
        client_kwargs={"scope": "openid"},
    )

    # Add type hinting
    oauth.innopolis: oauth.oauth2_client_cls  # noqa

    @router.get("/login")
    async def innopolis_login_or_register(redirect_uri: str, request: Request):
        ensure_allowed_redirect_uri(redirect_uri)
        request.session.clear()  # Clear session cookie as it is used only during auth
        request.session["redirect_uri"] = redirect_uri
        return await oauth.innopolis.authorize_redirect(request, redirect_uri)

    @router.get("/callback")
    async def innopolis_callback(
        request: Request,
        user_repository: Annotated[
            AbstractUserRepository, Depends(Dependencies.get_user_repository)
        ],
    ):
        # Check if there are any error from SSO
        error = request.query_params.get("error")
        if error:
            description = request.query_params.get("error_description")
            return JSONResponse(
                status_code=403, content={"error": error, "description": description}
            )
        try:
            token = await oauth.innopolis.authorize_access_token(request)
        except MismatchingStateError:
            # Session is different on 'login' and 'callback'
            return await recover_mismatching_state(request)

        user_info_dict: dict = token["userinfo"]

        user_info = UserInfoFromSSO(
            access_token=token["access_token"],
            refresh_token=token["refresh_token"],
            email=user_info_dict["email"],
            name=user_info_dict.get("commonname"),
            status=user_info_dict.get("Status"),
        )

        user = await user_repository.register_or_update_via_innopolis_sso(user_info)
        redirect_uri = request.session.pop("redirect_uri")
        ensure_allowed_redirect_uri(redirect_uri)
        request.session.clear()  # Clear session cookie as it is used only during auth
        token = TokenRepository.create_access_token(user.id)
        return redirect_with_token_as_cookie(redirect_uri, token)

    async def recover_mismatching_state(request: Request):
        redirect_uri = request.session.get("redirect_uri")

        try:
            # Check if a user has access token
            user_id = await get_current_user_id(
                token=request.cookies.get(settings.AUTH_COOKIE_NAME)
            )

        except (NoCredentialsException, IncorrectCredentialsException):
            user_id = None

        if redirect_uri and user_id:
            # User has already authenticated in another tab,
            # and we know where to return a user.
            # Let's get them where they want to be.
            ensure_allowed_redirect_uri(redirect_uri)
            return RedirectResponse(redirect_uri, status_code=302)

        if user_id is not None:
            # User has already authenticated in another tab,
            # but we don't know where to return a user.
            # Let's just return user to main page.
            return RedirectResponse(constants.WEBSITE_URL, status_code=302)

        if redirect_uri:
            # User is not authenticated,
            # and we know where to return a user after authentication.
            # Let's ask them to authenticate again.
            ensure_allowed_redirect_uri(redirect_uri)
            url = request.url_for("innopolis_login").include_query_params(
                redirect_uri=redirect_uri
            )
            return RedirectResponse(url, status_code=302)

        # We don't know anything, so let's just return user to main page.
        return RedirectResponse(constants.WEBSITE_URL, status_code=302)
