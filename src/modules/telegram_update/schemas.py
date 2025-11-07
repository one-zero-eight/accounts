from pydantic import BaseModel


class TelegramUpdateData(BaseModel):
    id: int
    updated_at: int
    success: bool
    status_code: int
    error_message: str | None = None

    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
