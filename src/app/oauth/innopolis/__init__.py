__all__ = ["router"]

from fastapi import APIRouter

router = APIRouter(prefix="/innopolis", tags=["Innopolis SSO"])

import src.app.oauth.telegram.routes  # noqa: E402, F401
