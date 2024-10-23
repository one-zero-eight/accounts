__all__ = ["SMTPRepository", "smtp_repository"]

import contextlib
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Generator

from email_validator import EmailNotValidError, validate_email

from src.config import settings

VERIFICATION_CODE_TEMPLATE = (Path(__file__).parent / "templates/verification-code.html").read_text()


# noinspection PyMethodMayBeStatic
class SMTPRepository:
    _server: smtplib.SMTP

    def __init__(self) -> None:
        self._server = smtplib.SMTP(settings.smtp.host, settings.smtp.port)

    @contextlib.contextmanager
    def _context(self) -> Generator[None, None, None]:
        self._server.connect(settings.smtp.host, settings.smtp.port)
        self._server.starttls()
        self._server.login(settings.smtp.username, settings.smtp.password.get_secret_value())
        yield
        self._server.quit()

    def render_verification_message(self, target_email: str, code: str) -> str:
        mail = MIMEMultipart("related")
        html = VERIFICATION_CODE_TEMPLATE.replace("${{code}}", code)
        msg_html = MIMEText(html, "html")
        mail.attach(msg_html)

        mail["Subject"] = "Verification code"
        mail["From"] = f"InNoHassle <{settings.smtp.username}>"
        mail["To"] = target_email

        return mail.as_string()

    def send(self, message: str, to: str):
        try:
            valid = validate_email(to)
            to = valid.normalized
        except EmailNotValidError as e:
            raise ValueError(e)
        with SMTPRepository._context(self):
            self._server.sendmail(settings.smtp.username, to, message)


if settings.smtp:
    smtp_repository: SMTPRepository = SMTPRepository()
else:
    import warnings

    warnings.warn("SMTP settings are not configured, SMTPRepository will not be available", RuntimeWarning)
