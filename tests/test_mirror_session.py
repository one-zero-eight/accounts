from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from beanie import PydanticObjectId
from fastapi import APIRouter, FastAPI, Request, Response
from httpx import ASGITransport, AsyncClient
from joserfc.jwk import RSAKey
from starlette.routing import Route

from src.api.dependencies import _get_user
from src.api.session import MIRROR_SESSION_KEY, MirrorAwareSessionMiddleware
from src.modules.mirror_session import router as mirror_session_router
from src.modules.tokens.repository import TokenRepository
from src.modules.users.repository import user_repository

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
def signing_key():
    return RSAKey.generate_key(2048)


@pytest.fixture
def user():
    return SimpleNamespace(id=PydanticObjectId(), innopolis_sso=None, telegram=None)


@pytest.fixture
def app(monkeypatch, signing_key, user):
    monkeypatch.setattr(TokenRepository, "private_jwt_key", signing_key)
    monkeypatch.setattr(TokenRepository, "public_jwt_key", RSAKey.import_key(signing_key.as_pem(private=False)))
    monkeypatch.setattr(user_repository, "exists", AsyncMock(return_value=True))

    async def login(request: Request) -> Response:
        request.session["uid"] = str(user.id)
        if request.query_params.get("impersonate"):
            request.session["impersonate_uid"] = str(user.id)
            request.session["impersonate_until"] = 9_999_999_999
        return Response(status_code=204)

    async def me(request: Request) -> Response:
        session = request.session
        return Response(
            content=f"{session.get('uid')} {bool(session.get(MIRROR_SESSION_KEY))}",
            media_type="text/plain",
        )

    application = FastAPI()
    application.add_middleware(
        MirrorAwareSessionMiddleware,
        secret_key="test-session-secret",
        session_cookie="session",
        https_only=True,
    )
    application.include_router(mirror_session_router)
    application.include_router(APIRouter(routes=[Route("/login", login), Route("/me", me)]))
    application.dependency_overrides[_get_user] = lambda: user
    return application


FRONTEND_ORIGIN = "https://innohassle.ru"


def make_client(app, origin: str | None = FRONTEND_ORIGIN):
    # The same app answers on both hosts: only the cookies of each client tell them apart.
    # Requests come from the frontend, so they carry its Origin like in a browser.
    headers = {"origin": origin} if origin is not None else {}
    return AsyncClient(transport=ASGITransport(app=app), base_url="https://accounts.test", headers=headers)


async def sign_in(client: AsyncClient) -> None:
    response = await client.get("/login")
    assert response.status_code == 204


async def transfer_token(client: AsyncClient) -> str:
    response = await client.post("/session/mirror/transfer-token")
    assert response.status_code == 200
    return response.json()["transfer_token"]


async def test_session_cookie_of_the_main_host_is_a_same_site_one(app):
    async with make_client(app) as client:
        response = await client.get("/login")
    cookie = response.headers["set-cookie"]
    assert "samesite=lax" in cookie
    assert "secure" in cookie
    assert "partitioned" not in cookie


async def test_mirror_session_cookie_is_cross_site(app, user):
    async with make_client(app) as main, make_client(app) as mirror:
        await sign_in(main)
        response = await mirror.post(
            "/session/mirror",
            json={"transfer_token": await transfer_token(main)},
        )
        assert response.status_code == 204
        cookie = response.headers["set-cookie"]
        assert "samesite=none" in cookie
        assert "secure" in cookie
        assert cookie.endswith("; partitioned")

        response = await mirror.get("/me")
        assert response.text == f"{user.id} True"


async def test_mirror_session_can_be_cleared_and_is_deleted_as_cross_site(app):
    async with make_client(app) as main, make_client(app) as mirror:
        await sign_in(main)
        await mirror.post("/session/mirror", json={"transfer_token": await transfer_token(main)})
        response = await mirror.delete("/session/mirror")
        assert response.status_code == 204
        cookie = response.headers["set-cookie"]
        assert cookie.startswith("session=null;")
        assert "samesite=none" in cookie
        assert cookie.endswith("; partitioned")

        assert (await mirror.get("/me")).text == "None False"


async def test_session_of_the_main_host_is_not_replaced_by_a_mirror_one(app, user):
    async with make_client(app) as main:
        await sign_in(main)
        response = await main.post(
            "/session/mirror",
            json={"transfer_token": await transfer_token(main)},
        )
        assert response.status_code == 204
        assert (await main.get("/me")).text == f"{user.id} False"


@pytest.mark.parametrize("origin", [None, "https://evil.example", "https://innohassle.ru.evil.example"])
async def test_mirror_session_is_not_set_from_a_disallowed_origin(app, user, origin):
    async with make_client(app) as main, make_client(app, origin=origin) as cross_site:
        await sign_in(main)
        response = await cross_site.post(
            "/session/mirror",
            json={"transfer_token": await transfer_token(main)},
        )
        assert response.status_code == 403
        assert "set-cookie" not in response.headers
        assert (await cross_site.get("/me")).text == "None False"


async def test_transfer_token_is_rejected_while_impersonating(app):
    async with make_client(app) as client:
        await client.get("/login", params={"impersonate": "1"})
        response = await client.post("/session/mirror/transfer-token")
    assert response.status_code == 403


async def test_invalid_transfer_token_does_not_open_a_session(app, user):
    async with make_client(app) as main, make_client(app) as mirror:
        await sign_in(main)
        token = await transfer_token(main)
        response = await mirror.post(
            "/session/mirror",
            json={"transfer_token": token[:-4] + "abcd"},
        )
        assert response.status_code == 401
        assert (await mirror.get("/me")).text == "None False"


async def test_transfer_token_of_a_deleted_user_does_not_open_a_session(app):
    async with make_client(app) as main, make_client(app) as mirror:
        await sign_in(main)
        token = await transfer_token(main)
        user_repository.exists.return_value = False
        response = await mirror.post("/session/mirror", json={"transfer_token": token})
    assert response.status_code == 401


def test_access_token_is_not_accepted_as_a_transfer_token(user):
    transfer_token = TokenRepository.create_mirror_transfer_token(user)
    access_token = TokenRepository.create_user_access_token(user)

    assert TokenRepository.verify_mirror_transfer_token(transfer_token) == str(user.id)
    assert TokenRepository.verify_mirror_transfer_token(access_token) is None


def test_expired_transfer_token_is_rejected(user):
    expired_token = TokenRepository._create_token(
        data={"uid": str(user.id)},
        expires_delta=timedelta(seconds=-1),
        aud=TokenRepository.MIRROR_TRANSFER_AUD,
    )
    assert TokenRepository.verify_mirror_transfer_token(expired_token) is None
