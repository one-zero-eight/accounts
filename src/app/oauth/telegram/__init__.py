__all__ = ["router"]

from fastapi import APIRouter

router = APIRouter(prefix="/telegram", tags=["Telegram"])

import src.app.oauth.telegram.routes  # noqa: E402, F401
