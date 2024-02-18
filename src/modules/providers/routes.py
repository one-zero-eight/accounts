from fastapi import APIRouter

from src.modules.providers.innopolis.routes import router as innopolis_router
from src.modules.providers.telegram.routes import router as telegram_router
from src.modules.providers.email.routes import router as email_router

router = APIRouter(prefix="/providers", tags=["Providers"])

router.include_router(innopolis_router)
router.include_router(telegram_router)
router.include_router(email_router)
