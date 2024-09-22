# Accounts API | InNoHassle ecosystem

> https://api.innohassle.ru/accounts

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

- [Python 3.12](https://www.python.org/downloads/) & [Poetry](https://python-poetry.org/docs/)
- [FastAPI](https://fastapi.tiangolo.com/) & [Pydantic](https://docs.pydantic.dev/latest/)
- Database and ORM: [MongoDB](https://www.mongodb.com/), [Beanie](https://beanie-odm.dev/)
- Formatting and linting: [Ruff](https://docs.astral.sh/ruff/), [pre-commit](https://pre-commit.com/)
- Deployment: [Docker](https://www.docker.com/), [Docker Compose](https://docs.docker.com/compose/),
  [GitHub Actions](https://github.com/features/actions)

## Development

### Getting started

1. Install [Python 3.12](https://www.python.org/downloads/)
2. Install [Poetry](https://python-poetry.org/docs/)
3. Install project dependencies with [Poetry](https://python-poetry.org/docs/cli/#options-2).
   ```bash
   poetry install
   ```
4. Set up [pre-commit](https://pre-commit.com/) hooks:

   ```bash
   poetry run pre-commit install --install-hooks -t pre-commit -t commit-msg
   ```
5. Set up project settings file (check [settings.schema.yaml](settings.schema.yaml) for more info).
   ```bash
   cp settings.example.yaml settings.yaml
   ```
   Edit `settings.yaml` according to your needs.
6. Set up a  [MongoDB](https://www.mongodb.com/) database instance.
   <details>
    <summary>Using docker container</summary>

    - Set up database settings for [docker-compose](https://docs.docker.com/compose/) in `.env` file:
      ```bash
      cp .env.example .env
      ```
    - Run the database instance:
      ```bash
      docker compose up -d db
      ```
    - Make sure to set up the actual database connection in `settings.yaml`, for example:
      ```yaml
      database:
        uri: mongodb://user:password@localhost:27017/db?authSource=admin
      ```

   </details>

**Set up PyCharm integrations**

1. Ruff ([plugin](https://plugins.jetbrains.com/plugin/20574-ruff)).
   It will lint and format your code. Make sure to enable `Use ruff format` option in plugin settings.
2. Pydantic ([plugin](https://plugins.jetbrains.com/plugin/12861-pydantic)). It will fix PyCharm issues with
   type-hinting.
3. Conventional commits ([plugin](https://plugins.jetbrains.com/plugin/13389-conventional-commit)). It will help you
   to write [conventional commits](https://www.conventionalcommits.org/en/v1.0.0/).

### Run for development

1. Run the database if you have not done it yet
2. Run the ASGI server
   ```bash
   poetry run python -m src.api
   ```
   OR using uvicorn directly
   ```bash
   poetry run uvicorn src.api.app:app --use-colors --proxy-headers --forwarded-allow-ips=*
   ```

Now the API is running on http://localhost:8000. Good job!

### Deployment

We use Docker with Docker Compose plugin to run the website on servers.

1. Copy the file with environment variables: `cp .env.example .env`
2. Change environment variables in the `.env` file
3. Copy the file with settings: `cp settings.example.yaml settings.yaml`
4. Change settings in the `settings.yaml` file according to your needs
   (check [settings.schema.yaml](settings.schema.yaml) for more info)
5. Install Docker with Docker Compose
6. Build a Docker image: `docker compose build --pull`
7. Run the container: `docker compose up --detach`
8. Check the logs: `docker compose logs -f`

## Contributing

We are open to contributions of any kind.
You can help us with code, bugs, design, documentation, media, new ideas, etc.
If you are interested in contributing, please read
our [contribution guide](https://github.com/one-zero-eight/.github/blob/main/CONTRIBUTING.md).
