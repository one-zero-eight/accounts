import hashlib
import hmac
from typing import Optional

from fastapi import Depends
from fastapi.responses import HTMLResponse, JSONResponse
from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel

from src.app.oauth.telegram import router
from src.app.oauth.telegram.dependencies import get_secret_key
from src.config import settings

env = Environment(
    loader=FileSystemLoader("src/app/oauth/telegram/templates"), autoescape=True
)

dummy_template_template = env.get_template("telegram-dummy.jinja2")


@router.get("/widget", response_class=HTMLResponse)
async def telegram_widget():
    return dummy_template_template.render(
        telegram_bot_name=settings.TELEGRAM_BOT_NAME,
    )


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
        return "\n".join(
            [
                f"{k}={getattr(self, k)}"
                for k in sorted(self.model_fields.keys())
                if k != "hash"
            ]
        )

    @property
    def encoded(self) -> bytes:
        return (
            self.string_to_hash.encode("utf-8")
            .decode("unicode-escape")
            .encode("ISO-8859-1")
        )


@router.post(
    "/connect",
    responses={200: {"description": "Success"}, 400: {"description": "Invalid hash"}},
    status_code=200,
)
async def telegram_connect(
    telegram_data: TelegramWidgetData, secret_key: bytes = Depends(get_secret_key)
):
    """
    Verify telegram data

    https://core.telegram.org/widgets/login#checking-authorization
    """
    received_hash = telegram_data.hash
    encoded_telegarm_data = telegram_data.encoded
    evaluated_hash = hmac.new(
        secret_key, encoded_telegarm_data, hashlib.sha256
    ).hexdigest()

    if evaluated_hash != received_hash:
        return JSONResponse(status_code=400, content={"detail": "Invalid hash"})
    return JSONResponse(status_code=200, content={"detail": "Success"})
