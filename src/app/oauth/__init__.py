__all__ = ["oauth", "router"]

from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter

router = APIRouter(tags=["Authorize"])
oauth = OAuth()

# Register all OAuth applications and routes
import src.app.oauth.logout  # noqa: E402, F401
import src.app.oauth.dev  # noqa: E402, F401
import src.app.oauth.routes  # noqa: E402, F401
from src.app.oauth.innopolis import router as innopolis_router  # noqa: E402, F401
from src.app.oauth.telegram import router as telegram_router  # noqa: E402, F401

router.include_router(innopolis_router)
router.include_router(telegram_router)
