from datetime import datetime, timezone, timedelta

from starlette.datastructures import URL
from starlette.responses import RedirectResponse

from src.config import settings
from src.exceptions import InvalidReturnToURL


def redirect_with_token_as_cookie(redirect_uri: str, token: str):
    response = RedirectResponse(redirect_uri, status_code=302)
    response.set_cookie(
        key=settings.AUTH_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=True,
        domain=settings.AUTH_COOKIE_DOMAIN,
        expires=datetime.now().astimezone(tz=timezone.utc) + timedelta(days=90),
    )
    return response


def redirect_deleting_token(redirect_uri: str):
    response = RedirectResponse(redirect_uri, status_code=302)
    response.delete_cookie(
        key=settings.AUTH_COOKIE_NAME,
        httponly=True,
        secure=True,
        domain=settings.AUTH_COOKIE_DOMAIN,
    )
    return response


def ensure_allowed_redirect_uri(redirect_uri: str):
    try:
        url = URL(redirect_uri)
        if url.hostname is None:
            return  # Ok. Allow returning to current domain
        if url.hostname in settings.AUTH_ALLOWED_DOMAINS:
            return  # Ok. Hostname is allowed (does not check port)
    except (AssertionError, ValueError):
        pass  # Bad. URL is malformed
    raise InvalidReturnToURL()
