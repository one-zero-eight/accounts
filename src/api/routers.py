from src.modules.providers.routes import router as router_web
from src.modules.users.routes import router as router_users
from src.modules.tokens.routes import router as router_tokens

routers = [router_web, router_users, router_tokens]

__all__ = ["routers"]
