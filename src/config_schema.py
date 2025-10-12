from enum import StrEnum
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, SecretStr


class Environment(StrEnum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"


class SettingsEntityModel(BaseModel):
    model_config = ConfigDict(use_attribute_docstrings=True, extra="forbid")


class InnopolisSSO(SettingsEntityModel):
    """Innopolis SSO settings (only for production)"""

    client_id: str
    "Client ID for Innopolis SSO"
    client_secret: SecretStr
    "Client secret for Innopolis SSO"
    redirect_uri: str
    "Redirect URI for Innopolis SSO"
    resource_id: str | None = None
    "Resource ID for Innopolis SSO (optional); Used for Sports API access"


class Telegram(SettingsEntityModel):
    bot_username: str
    "Bot username for Telegram"
    bot_token: SecretStr
    "Bot token for Telegram"


class Accounts(SettingsEntityModel):
    """InNoHassle Accounts integration settings"""

    api_url: str = "https://api.innohassle.ru/accounts/v0"
    "API URL for InNoHassle Accounts"
    api_jwt_token: SecretStr
    "JWT token for accessing the Accounts API as a service"


class Authentication(SettingsEntityModel):
    allowed_domains: list[str] = ["localhost", "127.0.0.1", "0.0.0.0"]
    "Allowed domains for redirecting after authentication"
    jwt_private_key: SecretStr
    "Private key for JWT. Use 'openssl genrsa -out private.pem 2048' to generate keys"
    jwt_public_key: str
    "Public key for JWT. Use 'openssl rsa -in private.pem -pubout -out public.pem' to generate keys"
    session_secret_key: SecretStr
    "Secret key for sessions. Use 'openssl rand -hex 32' to generate keys"


class SMTP(SettingsEntityModel):
    host: str
    "SMTP server host"
    port: int = 587
    "SMTP server port"
    username: str
    "SMTP server username"
    password: SecretStr
    "SMTP server password"


class Mongo(SettingsEntityModel):
    uri: SecretStr
    "MongoDB database connection URI"


class Settings(SettingsEntityModel):
    """
    Settings for the application. Get settings from `settings.yaml` file.
    """

    app_root_path: str = ""
    "Prefix for the API path (e.g. '/api/v0')"
    environment: Environment = Environment.DEVELOPMENT
    "App environment"
    mongo: Mongo
    "MongoDB settings"
    web_url: str
    "Web URL for the frontend part of InNoHassle-Accounts"
    cors_allow_origins: list[str] = ["https://innohassle.ru", "https://pre.innohassle.ru", "http://localhost:3000"]
    "Allowed origins for CORS: from which domains requests to the API are allowed"
    auth: Authentication
    "Authentication settings"
    innopolis_sso: InnopolisSSO | None = None
    "Innopolis SSO settings (only for production)"
    telegram: Telegram | None = None
    "Telegram settings"
    accounts: Accounts | None = None
    "Use production InNoHassle Accounts API for authentication in local development"
    smtp: SMTP | None = None
    "SMTP settings"

    @classmethod
    def from_yaml(cls, path: Path) -> "Settings":
        with open(path, encoding="utf-8") as f:
            yaml_config: dict = yaml.safe_load(f)
            yaml_config.pop("$schema", None)

        return cls.parse_obj(yaml_config)

    @classmethod
    def save_schema(cls, path: Path) -> None:
        with open(path, "w", encoding="utf-8") as f:
            schema = {"$schema": "https://json-schema.org/draft-07/schema", **cls.model_json_schema()}
            schema["properties"]["$schema"] = {
                "description": "Path to the schema file",
                "title": "Schema",
                "type": "string",
            }
            yaml.dump(schema, f, sort_keys=False)
