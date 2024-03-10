from src.modules.providers.routes import router as router_web
from src.modules.users.routes import router as router_users
from src.modules.tokens.routes import router as router_tokens
from src.modules.logout import router as router_logout

routers = [router_web, router_users, router_tokens, router_logout]

__all__ = ["routers"]
