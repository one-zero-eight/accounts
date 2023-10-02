__all__ = ["Oauth2Client"]

from typing import Optional

from sqlalchemy import String, ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from src.storages.sql.__mixin__ import IdMixin, UpdateCreateDateTimeMixin
from src.storages.sql.models.base import Base


class Oauth2Client(Base, UpdateCreateDateTimeMixin):
    __tablename__ = "oauth2_clients"

    client_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    client_secret: Mapped[str] = mapped_column(String(255), nullable=False)
    client_name: Mapped[str] = mapped_column(String(255), nullable=False)
    client_uri: Optional[Mapped[str]] = mapped_column(String(255), nullable=True)
    logo_uri: Optional[Mapped[str]] = mapped_column(String(255), nullable=True)
    contacts: Optional[Mapped[list[str]]] = mapped_column(
        ARRAY(String(255)), nullable=True
    )

    redirect_uris: Mapped[list[str]] = mapped_column(
        ARRAY(String(255)), nullable=False, server_default="{}"
    )
    default_scopes: Mapped[list[str]] = mapped_column(
        ARRAY(String(255)), nullable=False, server_default="{}"
    )
    grant_types: Mapped[list[str]] = mapped_column(
        ARRAY(String(255)), nullable=False, server_default="{authorization_code}"
    )
    # authorization_code, implicit, password, client_credentials, refresh_token

    response_types: Mapped[list[str]] = mapped_column(
        ARRAY(String(255)), nullable=False, server_default="{code}"
    )
    allowed_scopes: Mapped[list[str]] = mapped_column(
        ARRAY(String(255)), nullable=False, server_default="{}"
    )
    token_endpoint_auth_method: Mapped[str] = mapped_column(
        String(255), nullable=False, server_default="client_secret_basic"
    )
