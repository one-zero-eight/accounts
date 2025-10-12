"""
Providers for authentication or connectors of social accounts.
"""

from fastapi import APIRouter

from src.api import docs
from src.modules.providers.email.routes import router as email_router
from src.modules.providers.innohassle.routes import router as innohassle_accounts_router
from src.modules.providers.innopolis.routes import router as innopolis_router
from src.modules.providers.telegram.routes import router as telegram_router

router = APIRouter(prefix="/providers", tags=["Providers"])
docs.TAGS_INFO.append({"description": __doc__, "name": str(router.tags[0])})

router.include_router(innopolis_router)
router.include_router(telegram_router)
router.include_router(email_router)
router.include_router(innohassle_accounts_router)
