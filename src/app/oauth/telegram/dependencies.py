__all__ = ["get_secret_key"]

import hashlib

from src.config import settings


def get_secret_key() -> bytes:
    bot_token: str = settings.TELEGRAM_BOT_TOKEN.get_secret_value()
    secret_key = hashlib.sha256(bot_token.encode("utf-8"))  # noqa: HL
    return secret_key.digest()

