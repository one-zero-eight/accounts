# Accounts

> https://api.innohassle.ru/accounts/v0

[![GitHub Actions pre-commit](https://img.shields.io/github/actions/workflow/status/one-zero-eight/InNoHassle-Accounts/pre-commit.yaml?label=pre-commit)](https://github.com/one-zero-eight/InNoHassle-Accounts/actions)

[![Lines of Code](https://sonarcloud.io/api/project_badges/measure?project=one-zero-eight_InNoHassle-Accounts&metric=ncloc)](https://sonarcloud.io/summary/new_code?id=one-zero-eight_InNoHassle-Accounts)
[![Bugs](https://sonarcloud.io/api/project_badges/measure?project=one-zero-eight_InNoHassle-Accounts&metric=bugs)](https://sonarcloud.io/summary/new_code?id=one-zero-eight_InNoHassle-Accounts)
[![Vulnerabilities](https://sonarcloud.io/api/project_badges/measure?project=one-zero-eight_InNoHassle-Accounts&metric=vulnerabilities)](https://sonarcloud.io/summary/new_code?id=one-zero-eight_InNoHassle-Accounts)

## Table of contents

Did you know that GitHub supports table of
contents [by default](https://github.blog/changelog/2021-04-13-table-of-contents-support-in-markdown-files/) 🤔

## About

This is the API for accounts service in InNoHassle ecosystem.

### Features

- 🧑‍🔧 User Management
    - 🔑 Authenticate with Innopolis SSO
    - 📱 Connect Telegram account
    - ℹ️ Get user info
- 🛡️ Tokens
    - 🔒 Generate JWT tokens for other services in the ecosystem
    - ✅ Check token validity with public key

### Technologies

- [Python 3.12+](https://www.python.org/downloads/) & [uv](https://docs.astral.sh/uv/)
- [FastAPI](https://fastapi.tiangolo.com/) & [Pydantic](https://docs.pydantic.dev/latest/)
- Database and ORM: [MongoDB](https://www.mongodb.com/), [Beanie](https://beanie-odm.dev/)
- Formatting and linting: [Ruff](https://docs.astral.sh/ruff/), [pre-commit](https://pre-commit.com/)
- Deployment: [Docker](https://www.docker.com/), [Docker Compose](https://docs.docker.com/compose/),
  [GitHub Actions](https://github.com/features/actions)

## SDK

For other services in the InNoHassle ecosystem that need to interact with the Accounts API or with tokens from Accounts API, you can copy the SDK file from [`inh_accounts_sdk.py`](inh_accounts_sdk.py). This file is self-contained and can be used independently.

The SDK provides:
- `InNoHassleAccounts` class for API interactions
- JWT token decoding and validation
- User retrieval by ID, email, or Telegram ID
- Pydantic schemas for user data

> [!NOTE]
> The SDK file is designed to be copied into other projects.

## Development

### Set up for development

1. Install [uv](https://docs.astral.sh/uv/) and [Docker](https://docs.docker.com/engine/install/)
2. Install dependencies:
   ```bash
   uv sync
   ```
3. Prepare for development (read logs in the terminal):
   ```bash
   uv run -m src.prepare
   ```
   > Follow the provided instructions (if needed).
4. Start development server:
   ```bash
   uv run -m src.api --reload
   ```
   > Follow the provided instructions (if needed).
5. Open in the browser: http://localhost:8002.
   > The api will be reloaded when you edit the code

> [!IMPORTANT]
> For endpoints requiring authorization click "Authorize" button in Swagger UI

> [!TIP]
> Edit `settings.yaml` according to your needs, you can view schema in
> [config_schema.py](src/config_schema.py) and in [settings.schema.yaml](settings.schema.yaml)

**Set up PyCharm integrations**

1. Run configurations ([docs](https://www.jetbrains.com/help/pycharm/run-debug-configuration.html#createExplicitly)).
   Right-click the `__main__.py` file in the project explorer, select `Run '__main__'` from the context menu.
2. Ruff ([plugin](https://plugins.jetbrains.com/plugin/20574-ruff)).
   It will lint and format your code. Make sure to enable `Use ruff format` option in plugin settings.
3. Pydantic ([plugin](https://plugins.jetbrains.com/plugin/12861-pydantic)). It will fix PyCharm issues with
   type-hinting.
4. Conventional commits ([plugin](https://plugins.jetbrains.com/plugin/13389-conventional-commit)). It will help you
   to write [conventional commits](https://www.conventionalcommits.org/en/v1.0.0/).

### Deployment

We use Docker with Docker Compose plugin to run the service on servers.

1. Copy the file with environment variables: `cp .example.env .env`
2. Change environment variables in the `.env` file
3. Copy the file with settings: `cp settings.example.yaml settings.yaml`
4. Change settings in the `settings.yaml` file according to your needs
   (check [settings.schema.yaml](settings.schema.yaml) for more info)
5. Install Docker with Docker Compose
6. Run the containers: `docker compose up --build --wait`
7. Check the logs: `docker compose logs -f`

## FAQ

### Be up to date with the template!

Check https://github.com/one-zero-eight/fastapi-template for updates once in a while.

### How to update dependencies

1. Run `uv sync --upgrade` to update uv.lock file and install the latest versions of the dependencies.
2. Run `uv tree --outdated --depth=1` will show what package versions are installed and what are the latest versions.
3. Run `uv run pre-commit autoupdate`

Also, Dependabot will help you to keep your dependencies up-to-date, see [dependabot.yaml](.github/dependabot.yaml).

### How to dump the database

1. Dump:
   ```bash
   docker compose exec db sh -c 'mongodump "mongodb://$MONGO_INITDB_ROOT_USERNAME:$MONGO_INITDB_ROOT_PASSWORD@127.0.0.1:27017/db?authSource=admin" --db=db --out=dump/'
   ```
2. Restore:
   ```bash
   docker compose exec db sh -c 'mongorestore "mongodb://$MONGO_INITDB_ROOT_USERNAME:$MONGO_INITDB_ROOT_PASSWORD@127.0.0.1:27017/db?authSource=admin" --drop /dump/db'
   ```

## Contributing

We are open to contributions of any kind.
You can help us with code, bugs, design, documentation, media, new ideas, etc.
If you are interested in contributing, please read
our [contribution guide](https://github.com/one-zero-eight/.github/blob/main/CONTRIBUTING.md).
