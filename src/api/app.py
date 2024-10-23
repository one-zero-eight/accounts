__all__ = ["app"]

from fastapi import FastAPI
from fastapi_swagger import patch_fastapi
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

import src.logging_  # noqa: F401
from src.api import docs
from src.api.lifespan import lifespan
from src.config import settings
from src.config_schema import Environment

app = FastAPI(
    title=docs.TITLE,
    summary=docs.SUMMARY,
    description=docs.DESCRIPTION,
    version=docs.VERSION,
    contact=docs.CONTACT_INFO,
    license_info=docs.LICENSE_INFO,
    openapi_tags=docs.TAGS_INFO,
    servers=[
        {"url": settings.app_root_path, "description": "Current"},
    ],
    root_path=settings.app_root_path,
    root_path_in_servers=False,
    generate_unique_id_function=docs.generate_unique_operation_id,
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
    swagger_ui_oauth2_redirect_url=None,
)

patch_fastapi(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
same_site = "lax" if settings.environment == Environment.PRODUCTION else "none"
session_cookie = "__Secure-accounts-session" if settings.environment == Environment.PRODUCTION else "accounts-session"
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.auth.session_secret_key.get_secret_value(),
    session_cookie=session_cookie,
    max_age=14 * 24 * 60 * 60,  # 14 days, in seconds
    path=settings.app_root_path or "/",
    same_site=same_site,
    https_only=True,
    domain=None,
)

from src.modules.logout import router as router_logout  # noqa: E402
from src.modules.providers.routes import router as router_providers  # noqa: E402
from src.modules.tokens.routes import router as router_tokens  # noqa: E402
from src.modules.users.routes import router as router_users  # noqa: E402

app.include_router(router_providers)
app.include_router(router_users)
app.include_router(router_tokens)
app.include_router(router_logout)
