from typing import Any

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, SecurityScopes
from joserfc import jwt
from joserfc.errors import JoseError
from joserfc.jwk import RSAKey
from joserfc.jwt import JWTClaimsRegistry
from pydantic import BaseModel
from starlette import status

from src.api.dependencies import get_optional_admin_from_session
from src.config import settings

bearer_scheme = HTTPBearer(
    scheme_name="Bearer",
    description="Token from [InNoHassle Accounts](https://innohassle.ru/account/token), or from [#Tokens](http://127.0.0.1:8002/docs#/Tokens) if local development",
    bearerFormat="JWT",
    auto_error=False,  # We'll handle error manually
)
public_jwt_key = RSAKey.import_key(settings.auth.jwt_public_key)


async def get_token(bearer: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)) -> str | None:
    return bearer and bearer.credentials


async def verify_access_token(
    security_scopes: SecurityScopes, token: str | None = Depends(get_token)
) -> dict[str, Any]:
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = "Bearer"

    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No credentials provided",
            headers={"WWW-Authenticate": authenticate_value},
        )
    try:
        payload = jwt.decode(token, public_jwt_key)
        claims = payload.claims
        JWTClaimsRegistry().validate(claims)
        scope_string = claims.get("scope", None)
        scopes = scope_string.split() if scope_string else []
        for scope in security_scopes.scopes:
            by_prefix = ["users", "sport"]
            if scope in by_prefix:
                # check by prefix
                if not any(scope_.startswith(scope) for scope_ in scopes):
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail=f"Not enough permissions {scope}",
                        headers={"WWW-Authenticate": authenticate_value},
                    )
                continue

            if scope not in scopes:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Not enough permissions {scope}",
                    headers={"WWW-Authenticate": authenticate_value},
                )
    except JoseError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": authenticate_value},
        )
    return claims


class UsersAccess(BaseModel):
    is_admin: bool
    jwt_claims: dict[str, Any]


async def verify_users_scope_or_admin(
    request: Request,
    security_scopes: SecurityScopes,
    token: str | None = Depends(get_token),
) -> UsersAccess:
    if await get_optional_admin_from_session(request) is not None:
        return UsersAccess(is_admin=True, jwt_claims={})
    return UsersAccess(
        is_admin=False,
        jwt_claims=await verify_access_token(security_scopes, token),
    )


verify_access_token_responses = {
    401: {
        "description": "No credentials provided OR Not enough permissions (scopes) OR Could not validate credentials"
    },
}
