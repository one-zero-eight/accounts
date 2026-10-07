from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from beanie import PydanticObjectId
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from joserfc import jwt
from joserfc.jwk import RSAKey
from starlette.middleware.sessions import SessionMiddleware

from src.api.dependencies import _get_user
from src.modules.providers.innopolis.schemas import UserInfoFromSSO
from src.modules.tokens import dependencies
from src.modules.tokens.repository import TokenRepository
from src.modules.tokens.routes import AvailableScopes, router
from src.modules.users.repository import user_repository
from src.modules.users.routes import router as users_router

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
def signing_key():
    return RSAKey.generate_key(2048)


@pytest.fixture
async def token_client(monkeypatch, signing_key):
    def make_user():
        return SimpleNamespace(
            id=PydanticObjectId(),
            is_admin=False,
            innopolis_sso=UserInfoFromSSO(email="self@innopolis.university"),
            telegram=None,
            telegram_update_data=None,
            innohassle_admin=False,
            preferences=None,
        )

    user, other_user = make_user(), make_user()
    other_user.innopolis_sso.email = "other@innopolis.university"
    users = {user.id: user, other_user.id: other_user}

    async def get_user():
        return user

    monkeypatch.setattr(TokenRepository, "private_jwt_key", signing_key)
    monkeypatch.setattr(dependencies, "public_jwt_key", RSAKey.import_key(signing_key.as_pem(private=False)))
    monkeypatch.setattr(user_repository, "read", AsyncMock(side_effect=users.get))
    monkeypatch.setattr(
        user_repository, "wild_read", AsyncMock(side_effect=lambda **kwargs: users.get(kwargs["user_id"]))
    )
    monkeypatch.setattr(user_repository, "read_all_for_my_uni_export", AsyncMock(return_value=[]))
    app = FastAPI()
    app.add_middleware(SessionMiddleware, secret_key="test-session-secret")
    app.include_router(router)
    app.include_router(users_router)
    app.dependency_overrides[_get_user] = get_user
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client, user, other_user


@pytest.mark.parametrize("scopes", [["users:me"], ["sport:me"], ["users:me", "sport:me"]])
async def test_regular_user_can_create_personal_scope_tokens(token_client, signing_key, scopes):
    client, user, _ = token_client
    response = await client.get("/tokens/generate-service-token", params={"sub": "service", "scopes": scopes})

    assert response.status_code == 200
    claims = jwt.decode(response.json()["access_token"], signing_key).claims
    assert claims["scope"].split() == [scope.replace(":me", f":{user.id}") for scope in scopes]
    assert claims["sub"] == "service"


@pytest.mark.parametrize("scope", ["users", "sport", "parser", "my-uni"])
@pytest.mark.parametrize("include_personal_scope", [False, True])
async def test_regular_user_cannot_create_restricted_scope_tokens(token_client, scope, include_personal_scope):
    client, _, _ = token_client
    scopes = ["users:me", scope] if include_personal_scope else [scope]
    response = await client.get("/tokens/generate-service-token", params={"sub": "service", "scopes": scopes})

    assert response.status_code == 403


@pytest.mark.parametrize("scope", list(AvailableScopes))
async def test_admin_can_create_any_available_scope_token(token_client, signing_key, scope):
    client, user, _ = token_client
    user.is_admin = True
    response = await client.get("/tokens/generate-service-token", params={"sub": "service", "scopes": [scope]})

    assert response.status_code == 200
    claims = jwt.decode(response.json()["access_token"], signing_key).claims
    assert claims["scope"] == str(scope).replace(":me", f":{user.id}")


async def test_regular_user_cannot_create_default_users_scope_token(token_client):
    client, _, _ = token_client
    response = await client.get("/tokens/generate-service-token", params={"sub": "service"})

    assert response.status_code == 403


async def test_personal_users_token_can_read_only_its_owner(token_client):
    client, user, other_user = token_client
    response = await client.get("/tokens/generate-service-token", params={"sub": "service", "scopes": "users:me"})
    assert response.status_code == 200
    headers = {"Authorization": f"Bearer {response.json()['access_token']}"}

    response = await client.get(f"/users/by-id/{user.id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["id"] == str(user.id)
    response = await client.get(f"/users/by-id/{other_user.id}", headers=headers)
    assert response.status_code == 404


async def test_personal_sport_token_can_exchange_only_for_its_owner(token_client, signing_key):
    client, user, other_user = token_client
    response = await client.get("/tokens/generate-service-token", params={"sub": "service", "scopes": "sport:me"})
    assert response.status_code == 200
    headers = {"Authorization": f"Bearer {response.json()['access_token']}"}

    response = await client.get("/tokens/generate-sport-token", params={"innohassle_id": str(user.id)}, headers=headers)
    assert response.status_code == 200
    claims = jwt.decode(response.json()["access_token"], signing_key).claims
    assert claims["aud"] == "sport"
    assert claims["email"] == user.innopolis_sso.email
    response = await client.get(
        "/tokens/generate-sport-token", params={"innohassle_id": str(other_user.id)}, headers=headers
    )
    assert response.status_code == 403


@pytest.mark.parametrize("scopes", [["my-uni"], ["users", "my-uni"], ["my-uni", "sport"]])
async def test_my_uni_export_accepts_scope_among_multiple_scopes(token_client, scopes):
    client, user, _ = token_client
    user.is_admin = True
    response = await client.get("/tokens/generate-service-token", params={"sub": "service", "scopes": scopes})
    assert response.status_code == 200

    response = await client.get(
        "/users/bulk-export-for-my-uni", headers={"Authorization": f"Bearer {response.json()['access_token']}"}
    )
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.parametrize("sub", ["my-uni", "parser"])
async def test_personal_token_subject_does_not_grant_export_permissions(token_client, sub):
    client, _, _ = token_client
    response = await client.get("/tokens/generate-service-token", params={"sub": sub, "scopes": "users:me"})
    assert response.status_code == 200

    response = await client.get(
        "/users/bulk-export-for-my-uni", headers={"Authorization": f"Bearer {response.json()['access_token']}"}
    )
    assert response.status_code == 403


async def test_similar_scope_name_does_not_grant_export_permissions(token_client):
    client, _, _ = token_client
    token = TokenRepository.create_access_token("my-uni", ["users", "my-uni-extra"])
    response = await client.get("/users/bulk-export-for-my-uni", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403
