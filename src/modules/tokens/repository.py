__all__ = ["TokenRepository"]

from datetime import UTC, datetime, timedelta
from typing import Any

from beanie import PydanticObjectId
from joserfc import jwt
from joserfc.jwk import RSAKey

from src.config import settings
from src.storages.mongo.models import User


class TokenRepository:
    ALGORITHM = "RS256"
    private_jwt_key = RSAKey.import_key(settings.auth.jwt_private_key.get_secret_value())
    public_jwt_key = RSAKey.import_key(settings.auth.jwt_public_key)

    @classmethod
    def _create_token(
        cls, data: dict, expires_delta: timedelta, scopes: list[str] | None = None, aud: str | None = None
    ) -> str:
        payload = data.copy()
        issued_at = datetime.now(UTC)
        expire = issued_at + expires_delta
        payload.update({"exp": expire, "iat": issued_at})
        if scopes:
            payload["scope"] = " ".join(scopes)
        if aud:
            payload["aud"] = aud
        encoded_jwt = jwt.encode({"alg": cls.ALGORITHM}, payload, cls.private_jwt_key)
        return encoded_jwt.decode("utf-8") if isinstance(encoded_jwt, bytes) else encoded_jwt

    @classmethod
    def _generate_user_payload(cls, user: User) -> dict:
        data: dict = {"uid": str(user.id)}
        if user.innopolis_sso:
            data["email"] = user.innopolis_sso.email
        if user.telegram:
            data["telegram_id"] = user.telegram.id
        return data

    @classmethod
    def create_access_token(cls, sub: Any, scopes: list[str] | None) -> str:
        data = {"sub": str(sub)}
        access_token = TokenRepository._create_token(data=data, expires_delta=timedelta(days=90), scopes=scopes)
        return access_token

    @classmethod
    def create_user_access_token(cls, user: User) -> str:
        """
        Generate access token for current user with user id in `uid` field, expires in 1 day. Also will contain email, telegram_id if they are present.
        """
        data = TokenRepository._generate_user_payload(user)
        access_token = TokenRepository._create_token(data=data, expires_delta=timedelta(days=1), scopes=["me"])
        return access_token

    @classmethod
    def create_impersonation_token(cls, uid: str, email: str) -> str:
        data = {"uid": uid, "email": email}
        return TokenRepository._create_token(data=data, expires_delta=timedelta(days=1), scopes=["me"])

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
        return {"keys": [cls.public_jwt_key.as_dict(private=False)]}
