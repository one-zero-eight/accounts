from enum import StrEnum
from typing import Optional, Annotated

from fastapi import Query, Form
from pydantic import BaseModel

from src.app.oauth import router


@router.get(
    "/authorize",
)
async def authorize(
    response_type: str = Query(
        "code",
        enum=["code", "token", "id_token"],
        description="Tells the authorization server which grant to execute.",
    ),
    response_mode: Optional[str] = Query(
        "query",
        enum=["query", "fragment", "form_post", "web_message"],
        description="How the result of the authorization request is formatted.",
    ),
    client_id: str = Query(
        ..., description="The ID of the application that asks for authorization."
    ),
    redirect_uri: str = Query(
        ...,
        description="Holds a URL. A successful response from this endpoint results in a redirect to this URL.",
    ),
    scope: Optional[str] = Query(
        ...,
        description="A space-delimited list of permissions that the application requires.",
    ),
    audience: Optional[str] = Query(
        ...,
        description="The unique identifier of the API your web app wants to access."
    )
):
    ...


class GenerateTokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    refresh_token: Optional[str]
    id_token: Optional[str]


@router.post("/oauth/token")
async def generate_token(
    grant_type: str = Form(
        "authorization_code",
        description="The grant type. This field must contain the value authorization_code.",
    ),
    code: Optional[str] = Form(
        None,
        description="The authorization code that the client previously received from the authorization server.",
    ),
    client_id: Optional[str] = Form(
        None, description="The ID of the application that asks for authorization."
    ),
    client_secret: Optional[str] = Form(
        None, description="The secret of the application that asks for authorization."
    ),
    redirect_uri: Optional[str] = Form(
        None,
        description="The redirect URI of the application that asks for authorization.",
    ),
) -> GenerateTokenResponse:
    ...
