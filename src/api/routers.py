from src.modules.providers.routes import router as router_web
from src.modules.users.routes import router as router_users
from src.modules.clients.routes import router as router_clients
from src.modules.oauth.routes import router as router_oauth
from src.modules.resources.routes import router as router_resources

routers = [router_web, router_users, router_clients, router_oauth, router_resources]

__all__ = ["routers"]
