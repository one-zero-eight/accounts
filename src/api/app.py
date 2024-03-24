__all__ = ["app"]

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

import src.logging_  # noqa: F401
from src.api import docs
from src.api.lifespan import lifespan
from src.api.routers import routers
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
)

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

for router in routers:
    app.include_router(router)


# Redirect root to docs
@app.get("/", tags=["Root"], include_in_schema=False)
async def redirect_to_docs(request: Request):
    return RedirectResponse(url=request.url_for("swagger_ui_html"))


@app.get("/docs", tags=["System"], include_in_schema=False)
async def swagger_ui_html(request: Request):
    from fastapi.openapi.docs import get_swagger_ui_html

    root_path = request.scope.get("root_path", "").rstrip("/")
    openapi_url = root_path + app.openapi_url

    return get_swagger_ui_html(
        openapi_url=openapi_url,
        title=app.title + " - Swagger UI",
        swagger_js_url="https://api.innohassle.ru/swagger/swagger-ui-bundle.js",
        swagger_css_url="https://api.innohassle.ru/swagger/swagger-ui.css",
        swagger_favicon_url="https://api.innohassle.ru/swagger/favicon.png",
        swagger_ui_parameters={"tryItOutEnabled": True, "persistAuthorization": True, "filter": True},
    )
