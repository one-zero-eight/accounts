__all__ = ["MIRROR_SESSION_KEY", "MirrorAwareSessionMiddleware"]

import re

from starlette.middleware.sessions import SessionMiddleware
from starlette.types import ASGIApp, Message, Receive, Scope, Send

# Session key that marks a session created on a mirror host (see src/modules/mirror_session)
MIRROR_SESSION_KEY = "mirror"
# Scope key that remembers a request came with a mirror session, so the cookie of a session cleared by the
# response is still written as a cross-site one
_MIRROR_SCOPE_KEY = "mirror_session"


class MirrorAwareSessionMiddleware(SessionMiddleware):
    """
    Session middleware that writes the cookie of a mirror session as a cross-site one.

    A mirror host is another site than the frontend, so the browser accepts and sends its cookie only with
    `SameSite=None` and keeps it only when it is `Partitioned`, i.e. stored for the frontend's site.
    """

    def __init__(self, app: ASGIApp, **kwargs) -> None:
        super().__init__(app, **kwargs)
        self.inner_app = app
        # Runs inside the session middleware, where the session is already loaded from the cookie
        self.app = self.remember_mirror_session

    async def remember_mirror_session(self, scope: Scope, receive: Receive, send: Send) -> None:
        if self.is_mirror_session(scope):
            scope[_MIRROR_SCOPE_KEY] = True
        await self.inner_app(scope, receive, send)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start" and self.is_mirror_session(scope):
                message["headers"] = [
                    (name, self.as_cross_site_cookie(value) if self.is_session_cookie(name, value) else value)
                    for name, value in message["headers"]
                ]
            await send(message)

        await super().__call__(scope, receive, send_wrapper)

    @staticmethod
    def is_mirror_session(scope: Scope) -> bool:
        session = scope.get("session") or {}
        return bool(scope.get(_MIRROR_SCOPE_KEY) or session.get(MIRROR_SESSION_KEY))

    def is_session_cookie(self, name: bytes, value: bytes) -> bool:
        return name.lower() == b"set-cookie" and value.startswith(f"{self.session_cookie}=".encode())

    @staticmethod
    def as_cross_site_cookie(value: bytes) -> bytes:
        # SameSite=None lets a request between sites carry the cookie, Partitioned (CHIPS) lets the browser keep
        # such a cookie at all.
        relaxed = re.sub(rb"; samesite=\w+", b"; samesite=none", value, flags=re.IGNORECASE)
        return relaxed + b"; partitioned"
