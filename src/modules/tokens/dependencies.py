from authlib.jose import jwt, JoseError, JWTClaims
from fastapi import HTTPException, Depends
from fastapi.security import SecurityScopes, HTTPAuthorizationCredentials, HTTPBearer
from starlette import status

from src.config import settings

bearer_scheme = HTTPBearer(
    scheme_name="Bearer",
    description="Your JSON Web Token (JWT)",
    bearerFormat="JWT",
    auto_error=False,  # We'll handle error manually
)


async def get_token(bearer: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)) -> str | None:
    return bearer and bearer.credentials


async def verify_access_token(security_scopes: SecurityScopes, token: str | None = Depends(get_token)) -> JWTClaims:
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
        payload = jwt.decode(token, settings.auth.jwt_public_key)
        scope_string = payload.get("scope", None)
        scopes = scope_string.split() if scope_string else []
        for scope in security_scopes.scopes:
            if scope == "users":
                # check by prefix
                if not any(scope_.startswith("users") for scope_ in scopes):
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
    return payload


verify_access_token_responses = {
    401: {
        "description": "No credentials provided OR Not enough permissions (scopes) OR Could not validate credentials"
    },
}
