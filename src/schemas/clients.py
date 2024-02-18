from typing import Optional

from pydantic import BaseModel, Field, ConfigDict

from src.schemas.oauth2 import GrantTypes, ResponseTypes


class CreateOauth2Client(BaseModel):
    client_name: str
    """Name of the client"""
    client_uri: Optional[str] = None
    """URL to the home page of the client"""
    logo_uri: Optional[str] = None
    """URL to the logo of the client"""
    contacts: Optional[list[str]] = None
    """List of contacts of the client"""
    redirect_uris: list[str] = Field(default_factory=list)
    """List of allowed redirect URIs"""
    grant_types: list[GrantTypes] = Field(default_factory=lambda: [GrantTypes.authorization_code])
    """List of allowed grant types"""
    response_types: list[ResponseTypes] = Field(default_factory=lambda: [ResponseTypes.code])
    """List of allowed response types"""
    allowed_scopes: list[str] = Field(default_factory=list)
    """List of allowed scopes"""
    default_scopes: list[str] = Field(default_factory=list)
    """List of default scopes"""

    token_endpoint_auth_method: str = Field(
        default="client_secret_basic",
        description="client_secret_basic, client_secret_post, client_secret_jwt, private_key_jwt, none",
    )


class ViewOauth2Client(BaseModel):
    client_id: str
    client_name: str
    client_uri: Optional[str] = None
    logo_uri: Optional[str] = None
    contacts: Optional[list[str]] = None
    redirect_uris: list[str]
    grant_types: list[GrantTypes]
    response_types: list[ResponseTypes]
    allowed_scopes: list[str]
    default_scopes: list[str]
    token_endpoint_auth_method: str

    model_config = ConfigDict(from_attributes=True)


# sql.models.clients.Oauth2Client
# from typing import Optional
#
# from sqlalchemy import String, ARRAY
# from sqlalchemy.orm import Mapped, mapped_column
#
# from src.storages.sql.__mixin__ import IdMixin, UpdateCreateDateTimeMixin
# from src.storages.sql.models.base import Base
#
#
# class Oauth2Client(Base, IdMixin, UpdateCreateDateTimeMixin):
#     __tablename__ = "oauth2_clients"
#
#     client_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
#     client_secret: Mapped[str] = mapped_column(String(255), nullable=False)
#     client_name: Mapped[str] = mapped_column(String(255), nullable=False)
#     client_uri: Optional[Mapped[str]] = mapped_column(String(255), nullable=True)
#     logo_uri: Optional[Mapped[str]] = mapped_column(String(255), nullable=True)
#     contacts: Optional[Mapped[list[str]]] = mapped_column(
#         ARRAY(String(255)), nullable=True
#     )
#
#     redirect_uris: Mapped[list[str]] = mapped_column(
#         ARRAY(String(255)), nullable=False, server_default="{}"
#     )
#     default_scopes: Mapped[list[str]] = mapped_column(
#         ARRAY(String(255)), nullable=False, server_default="{}"
#     )
#     grant_types: Mapped[list[str]] = mapped_column(
#         ARRAY(String(255)), nullable=False, server_default="{authorization_code}"
#     )
#     # authorization_code, implicit, password, client_credentials, refresh_token
#
#     response_types: Mapped[list[str]] = mapped_column(
#         ARRAY(String(255)), nullable=False, server_default="{code}"
#     )
#     # code, token
#     allowed_scopes: Mapped[list[str]] = mapped_column(
#         ARRAY(String(255)), nullable=False, server_default="{}"
#     )
#     token_endpoint_auth_method: Mapped[str] = mapped_column(
#         String(255), nullable=False, server_default="client_secret_basic"
#     )
