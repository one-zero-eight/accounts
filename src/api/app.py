__all__ = ["app"]

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from src.api import docs
from src.api.lifespan import lifespan
from src.api.routers import routers
from src.config import settings

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
    swagger_ui_oauth2_redirect_url=None,
    swagger_ui_parameters={"tryItOutEnabled": True, "persistAuthorization": True, "filter": True},
    generate_unique_id_function=docs.generate_unique_operation_id,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
same_site = "lax" if settings.environment == "production" else "none"
app.add_middleware(
    SessionMiddleware,
    same_site=same_site,
    secret_key=settings.auth.session_secret_key.get_secret_value(),
    https_only=True,
)

for router in routers:
    app.include_router(router)


# Redirect root to docs
@app.get("/", tags=["Root"], include_in_schema=False)
async def redirect_to_docs(request: Request):
    return RedirectResponse(url=request.url_for("swagger_ui_html"))
