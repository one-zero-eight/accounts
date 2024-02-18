from enum import StrEnum
from typing import Optional, Annotated

from fastapi import Query, Form, APIRouter, Depends
from pydantic import BaseModel, Field, RootModel

from src.api.dependencies import Shared
from src.modules.clients.repository import ClientRepository
from src.modules.resources.repository import ResourceRepository

router = APIRouter(prefix="/oauth2", tags=["Oauth 2"])


class CodeChallenge(StrEnum):
    S256 = "S256"

    @classmethod
    def enum(cls):
        return [cls.S256]


class ResponseType(StrEnum):
    CODE = "code"
    TOKEN = "token"
    ID_TOKEN = "id_token"

    @classmethod
    def enum(cls):
        return [cls.CODE, cls.TOKEN, cls.ID_TOKEN]


ResponseTypesModel = RootModel[set[ResponseType]]


class ResponseMode(StrEnum):
    # QUERY = "query"
    FRAGMENT = "fragment"

    # FORM_POST = "form_post"
    # WEB_MESSAGE = "web_message"

    @classmethod
    def enum(cls):
        # return [cls.QUERY, cls.FRAGMENT, cls.FORM_POST, cls.WEB_MESSAGE]
        return [cls.FRAGMENT]


class AuthorizeMethodSchema(BaseModel):
    response_type: str = Field(
        Query(
            ResponseType.CODE,
            description="Tells the authorization server which grant to execute (delimited by spaces).",
        ),
        examples=["code", "token", "id_token", "code token", "code id_token", "token id_token", "code token id_token"],
    )
    response_mode: str = Field(
        Query(
            ResponseMode.FRAGMENT,
            enum=ResponseMode.enum(),
            description="How the result of the authorization request is formatted.",
        )
    )
    client_id: str = Field(Query(..., description="The ID of the application that asks for authorization."))
    redirect_uri: str = Field(
        Query(
            ..., description="Holds a URL. A successful response from this endpoint results in a redirect to this URL."
        ),
    )
    scope: Optional[str] = Field(
        Query(..., description="A space-delimited list of permissions that the application requires.")
    )
    audience: Optional[str] = Field(
        Query(..., description="The unique identifier of the API your web app wants to access.")
    )
    code_challenge: Optional[str] = Field(
        Query(None, description="A code challenge for PKCE. This is a transformation of the code verifier.")
    )
    code_challenge_method: Optional[str] = Field(
        Query(
            None,
            enum=CodeChallenge.enum(),
            description="The method used to transform the code verifier in the code challenge.",
        )
    )


@router.get("/authorize")
async def authorize(schema: Annotated[AuthorizeMethodSchema, Depends()]):
    if bool(schema.code_challenge) != bool(schema.code_challenge_method):
        raise ValueError("Both code_challenge and code_challenge_method must be present or absent")

    use_pkce = schema.code_challenge is not None and schema.code_challenge_method is not None
    response_types = ResponseTypesModel.model_validate(schema.response_type.split(" "))
    # validate response_type

    is_authorization_code_flow = ResponseType.CODE in response_types

    client_repository = Shared.f(ClientRepository)
    client = await client_repository.read(schema.client_id)
    # check if valid client
    if client is None:
        raise ValueError("Client not found")
    # check if redirect_uri is allowed for the client
    if schema.redirect_uri not in client.allowed_redirect_uris:
        raise ValueError("Redirect URI not allowed for the client")

    resource_repository = Shared.f(ResourceRepository)
    resource = await resource_repository.read(schema.audience)
    # check if valid resource
    if resource is None:
        raise ValueError("Resource not found")

    # check if scope is allowed for the client
    scopes = schema.scope.split(" ")
    for scope in scopes:
        if scope not in resource.scopes:
            raise ValueError("Unknown scope for resource")
        scope_settings = resource.scopes[scope]
        if scope_settings and scope_settings.client_id != client.client_id:
            raise ValueError("Scope not allowed for the client")



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
    client_id: Optional[str] = Form(None, description="The ID of the application that asks for authorization."),
    client_secret: Optional[str] = Form(None, description="The secret of the application that asks for authorization."),
    redirect_uri: Optional[str] = Form(
        None,
        description="The redirect URI of the application that asks for authorization.",
    ),
    code_verifier: Optional[str] = Form(
        None,
        description="The code verifier that the client previously sent to the authorization server.",
    ),
) -> GenerateTokenResponse:
    ...
