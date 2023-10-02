from src.app.oauth import router
from src.app.oauth.redirect import redirect_deleting_token, ensure_allowed_redirect_uri


@router.get("/logout", include_in_schema=False)
async def logout(redirect_uri: str):
    ensure_allowed_redirect_uri(redirect_uri)
    return redirect_deleting_token(redirect_uri)
