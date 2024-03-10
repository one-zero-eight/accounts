from fastapi import APIRouter, Request
from starlette.responses import RedirectResponse

from src.exceptions import InvalidReturnToURL
from src.modules.providers.innopolis.routes import ensure_allowed_redirect_uri

router = APIRouter()


@router.get(
    "/logout",
    responses={302: {"description": "Redirect to the specified URL"}, **InvalidReturnToURL.responses},
)
async def logout(redirect_uri: str, request: Request):
    ensure_allowed_redirect_uri(redirect_uri)
    request.session.clear()  # Clear session cookie as it is used only during auth
    return RedirectResponse(redirect_uri, status_code=302)
