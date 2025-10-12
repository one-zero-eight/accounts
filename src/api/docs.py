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

TAGS_INFO: list[dict] = []
'''
On each new tag add description to TAGS_INFO, f.e.

```python
"""
Some description of the module with new tag.
"""
docs.TAGS_INFO.append({"description": __doc__, "name": str(router.tags[0])})
```

'''
