__all__ = ["TelegramWidgetData", "TelegramLoginResponse"]

from typing import Optional

from pydantic import BaseModel


class TelegramWidgetData(BaseModel):
    hash: str
    id: int
    auth_date: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    photo_url: Optional[str] = None

    @property
    def string_to_hash(self) -> str:
        return "\n".join([f"{k}={getattr(self, k)}" for k in sorted(self.model_fields.keys()) if k != "hash"])

    @property
    def encoded(self) -> bytes:
        return self.string_to_hash.encode("utf-8").decode("unicode-escape").encode("ISO-8859-1")


class TelegramLoginResponse(BaseModel):
    need_to_connect: bool
