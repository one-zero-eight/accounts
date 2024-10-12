# Website url
import re

from fastapi.routing import APIRoute

WEBSITE_URL = "https://innohassle.ru"

# API version
VERSION = "0.1.0"

# Info for OpenAPI specification
TITLE = "InNoHassle Accounts API"
SUMMARY = "Register, login and manage your account in InNoHassle ecosystem."

DESCRIPTION = """
### About this project

This is the API for Accounts project in InNoHassle ecosystem developed by one-zero-eight community.

Using this API you can manage user accounts and receive access tokens for other APIs.

Backend is developed using FastAPI framework on Python.

Note: API is unstable. Endpoints and models may change in the future.

Useful links:
- [Accounts API source code](https://github.com/one-zero-eight/accounts)
- [InNoHassle Website](https://innohassle.ru/)
"""

CONTACT_INFO = {
    "name": "one-zero-eight (Telegram)",
    "url": "https://t.me/one_zero_eight",
}
LICENSE_INFO = {
    "name": "MIT License",
    "identifier": "MIT",
}

TAGS_INFO = [
    {
        "name": "Users",
        "description": "User data and linking users with event groups.",
    },
    {
        "name": "Tokens",
        "description": (
            "Generate access tokens to call other APIs. "
            "'My token' is for frontend which can access any API from the name of user. "
            "'Service tokens' are for backend programs which can access data of multiple users."
        ),
    },
    {
        "name": "Providers",
        "description": "Providers for authentication or connectors of social accounts.",
    },
]


def generate_unique_operation_id(route: APIRoute) -> str:
    # Better names for operationId in OpenAPI schema.
    # It is needed because clients generate code based on these names.
    # Requires pair (tag name + function name) to be unique.
    # See fastapi.utils:generate_unique_id (default implementation).
    if route.tags:
        operation_id = f"{route.tags[0]}_{route.name}".lower()
    else:
        operation_id = route.name.lower()
    operation_id = re.sub(r"\W+", "_", operation_id)
    return operation_id
