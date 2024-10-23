__all__ = ["TokenRepository"]

from datetime import datetime, timedelta
from typing import Any

from authlib.jose import JsonWebKey, jwt
from beanie import PydanticObjectId

from src.config import settings


class TokenRepository:
    ALGORITHM = "RS256"

    @classmethod
    def _create_token(
        cls, data: dict, expires_delta: timedelta, scopes: list[str] | None = None, aud: str | None = None
    ) -> str:
        payload = data.copy()
        issued_at = datetime.utcnow()
        expire = issued_at + expires_delta
        payload.update({"exp": expire, "iat": issued_at})
        if scopes:
            payload["scope"] = " ".join(scopes)
        if aud:
            payload["aud"] = aud
        encoded_jwt = jwt.encode({"alg": cls.ALGORITHM}, payload, settings.auth.jwt_private_key.get_secret_value())
        return str(encoded_jwt, "utf-8")

    @classmethod
    def create_access_token(cls, sub: Any, scopes: list[str] | None) -> str:
        data = {"sub": str(sub)}
        access_token = TokenRepository._create_token(data=data, expires_delta=timedelta(days=90), scopes=scopes)
        return access_token

    @classmethod
    def create_user_access_token(cls, user_id: PydanticObjectId) -> str:
        data = {"uid": str(user_id)}
        access_token = TokenRepository._create_token(data=data, expires_delta=timedelta(days=1), scopes=["me"])
        return access_token

    @classmethod
    def create_sport_user_access_token(cls, email: str) -> str:
        data = {"email": email}
        access_token = TokenRepository._create_token(data=data, expires_delta=timedelta(days=1), aud="sport")
        return access_token

    @classmethod
    def create_email_flow_token(cls, email_flow_id: PydanticObjectId) -> str:
        data = {"email_flow_id": str(email_flow_id)}
        access_token = TokenRepository._create_token(data=data, expires_delta=timedelta(hours=1))
        return access_token

    @classmethod
    def get_jwks(cls) -> dict:
        jwk = JsonWebKey.import_key(
            settings.auth.jwt_public_key, {"kty": "RSA", "alg": "RS256", "use": "sig", "kid": "public"}
        )
        return {"keys": [jwk.as_dict()]}
