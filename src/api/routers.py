from src.config import settings
from src.config_schema import Environment
from src.modules.providers.routes import router as router_web
from src.modules.users.routes import router as router_users
from src.modules.clients.routes import router as router_clients
from src.modules.resources.routes import router as router_resources

routers = [router_web, router_users, router_clients, router_resources]

# feauture flag
if settings.environment == Environment.DEVELOPMENT:
    from src.modules.oauth.routes import router as router_oauth

    routers.append(router_oauth)

__all__ = ["routers"]
