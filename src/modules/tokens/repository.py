__all__ = ["TokenRepository"]

from datetime import timedelta, datetime

from authlib.jose import jwt

from src.config import settings
from beanie import PydanticObjectId


class TokenRepository:
    ALGORITHM = "RS256"

    @classmethod
    def _create_token(cls, data: dict, expires_delta: timedelta) -> str:
        payload = data.copy()
        issued_at = datetime.utcnow()
        expire = issued_at + expires_delta
        payload.update({"exp": expire, "iat": issued_at})
        encoded_jwt = jwt.encode({"alg": cls.ALGORITHM}, payload, settings.auth.jwt_private_key.get_secret_value())
        return str(encoded_jwt, "utf-8")

    @classmethod
    def create_access_token(cls, user_id: int) -> str:
        data = {"sub": str(user_id)}
        access_token = TokenRepository._create_token(data=data, expires_delta=timedelta(days=90))
        return access_token

    @classmethod
    def create_email_flow_token(cls, email_flow_id: PydanticObjectId) -> str:
        data = {"email_flow_id": str(email_flow_id)}
        access_token = TokenRepository._create_token(data=data, expires_delta=timedelta(hours=1))
        return access_token
