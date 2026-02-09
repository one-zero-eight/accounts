import os
import shutil
import subprocess
from pathlib import Path

import yaml

BASE_DIR = Path(__file__).resolve().parents[1]
SETTINGS_TEMPLATE = BASE_DIR / "settings.example.yaml"
SETTINGS_FILE = BASE_DIR / "settings.yaml"
PRE_COMMIT_CONFIG = BASE_DIR / ".pre-commit-config.yaml"


def get_settings():
    """
    Load and return the settings from `settings.yaml` if it exists.
    """
    if not SETTINGS_FILE.exists():
        raise RuntimeError("❌ No `settings.yaml` found.")

    try:
        with open(SETTINGS_FILE) as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        raise RuntimeError("❌ No `settings.yaml` found.") from e


def ensure_settings_file():
    """
    Ensure `settings.yaml` exists. If not, copy `settings.example.yaml`.
    """
    if not SETTINGS_TEMPLATE.exists():
        print("❌ No `settings.example.yaml` found. Skipping copying.")
        return

    if SETTINGS_FILE.exists():
        print("✅ `settings.yaml` exists.")
        return

    shutil.copy(SETTINGS_TEMPLATE, SETTINGS_FILE)
    print(f"✅ Copied `{SETTINGS_TEMPLATE}` to `{SETTINGS_FILE}`")


def ensure_pre_commit_hooks():
    """
    Ensure `pre-commit` hooks are installed.
    """

    def is_pre_commit_installed():
        pre_commit_hook = BASE_DIR / ".git" / "hooks" / "pre-commit"
        return pre_commit_hook.exists() and os.access(pre_commit_hook, os.X_OK)

    if not PRE_COMMIT_CONFIG.exists():
        print("❌ No `.pre-commit-config.yaml` found. Skipping pre-commit setup.")
        return

    if is_pre_commit_installed():
        print("✅ Pre-commit hooks are installed.")
        return

    try:
        subprocess.run(
            ["poetry", "run", "pre-commit", "install", "--install-hooks", "-t", "pre-commit", "-t", "commit-msg"],
            check=True,
            text=True,
        )
        print("✅ Pre-commit hooks installed successfully.")
    except subprocess.CalledProcessError as e:
        print(
            f"❌ Error setting up pre-commit hooks:\n{e.stderr}\n  Please, setup it manually with `poetry run pre-commit install --install-hooks -t pre-commit -t commit-msg`"
        )


def check_database_access():
    """
    Ensure the database is accessible using `database_uri` from `settings.yaml`. If missing, set a default value.
    """
    import asyncio

    from motor.motor_asyncio import AsyncIOMotorClient
    from pymongo import timeout

    settings = get_settings()
    database_uri = settings.get("mongo", {}).get("uri")

    def get_docker_compose_command():
        commands = ["docker compose", "docker-compose"]

        for cmd in commands:
            try:
                subprocess.run(cmd.split(), check=True, text=True, capture_output=True)
                return cmd
            except subprocess.CalledProcessError:
                # Command not available
                continue
        return None

    async def test_connection():
        try:
            motor_client = AsyncIOMotorClient(database_uri)
            motor_client.get_io_loop = asyncio.get_running_loop  # type: ignore[method-assign]

            with timeout(2):
                await motor_client.server_info()
                print("✅ Successfully connected to the database.")
        except Exception:
            print(f"⚠️ Failed to connect to the database at `{database_uri}`")
            docker_compose = get_docker_compose_command()

            if docker_compose:
                print(f"  ➡ Attempting to start the database using `{docker_compose} up -d db` (wait for it)")
                try:
                    subprocess.run(
                        [*docker_compose.split(), "up", "-d", "--wait", "db"],
                        check=True,
                        text=True,
                        capture_output=True,
                    )
                    print(f"  ✅ `{docker_compose} up -d db` executed successfully. Retrying connection...")
                    # Retry the database connection after starting the container
                    motor_client = AsyncIOMotorClient(database_uri)
                    motor_client.get_io_loop = asyncio.get_running_loop  # type: ignore[method-assign]

                    with timeout(2):
                        await motor_client.server_info()
                        print("  ✅ Successfully connected to the database after starting the container.")
                except subprocess.CalledProcessError as docker_error:
                    print(f"  ❌ Failed to start the database using `{docker_compose} up -d db`:\n  {docker_error}")
                except Exception as retry_error:
                    print(f"  ❌ Retried database connection but failed again:\n  {retry_error}")
            else:
                print("  ❌ Docker Compose is not available, so not able to start db automatically.")

    asyncio.run(test_connection())


def ensure_auth_settings():
    """
    Ensure `auth` settings are configured in `settings.yaml`.
    Generate session_secret_key, jwt_private_key, and jwt_public_key if missing.
    """
    import re
    import secrets

    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    settings = get_settings()
    auth = settings.get("auth", {})

    session_secret_key = auth.get("session_secret_key")
    jwt_private_key = auth.get("jwt_private_key")
    jwt_public_key = auth.get("jwt_public_key")

    placeholder_patterns = ["...", "null", "x" * 32, "s" * 20]

    def is_placeholder(value):
        if not value or value == "...":
            return True
        if isinstance(value, str):
            return any(pattern in value for pattern in placeholder_patterns)
        return False

    needs_update = False

    if is_placeholder(session_secret_key):
        print("⚠️ `auth.session_secret_key` is missing. Generating...")
        try:
            new_key = secrets.token_hex(32)

            with open(SETTINGS_FILE) as f:
                content = f.read()

            content = re.sub(r"session_secret_key:\s*[^\n]*", f"session_secret_key: {new_key}", content)

            with open(SETTINGS_FILE, "w") as f:
                f.write(content)

            needs_update = True
            print("  ✅ Generated `session_secret_key`.")
        except Exception as e:
            print(f"  ❌ Error generating session_secret_key: {e}")
    else:
        print("✅ `auth.session_secret_key` is specified.")

    if is_placeholder(jwt_private_key) or is_placeholder(jwt_public_key):
        print("⚠️ `auth.jwt_private_key` or `auth.jwt_public_key` is missing. Generating...")
        try:
            private_key_obj = rsa.generate_private_key(public_exponent=65537, key_size=2048, backend=default_backend())

            private_key = (
                private_key_obj.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.TraditionalOpenSSL,
                    encryption_algorithm=serialization.NoEncryption(),
                )
                .decode("utf-8")
                .strip()
            )

            public_key = (
                private_key_obj.public_key()
                .public_bytes(
                    encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo
                )
                .decode("utf-8")
                .strip()
            )

            with open(SETTINGS_FILE) as f:
                content = f.read()

            private_key_indented = "\n    ".join(private_key.split("\n"))
            public_key_indented = "\n    ".join(public_key.split("\n"))

            content = re.sub(
                r"jwt_private_key:\s*\|?\s*\n(?:    [^\n]*\n)*",
                f"jwt_private_key: |\n    {private_key_indented}\n",
                content,
            )

            content = re.sub(
                r"jwt_public_key:\s*\|?\s*\n(?:    [^\n]*\n)*",
                f"jwt_public_key: |\n    {public_key_indented}\n",
                content,
            )

            with open(SETTINGS_FILE, "w") as f:
                f.write(content)

            needs_update = True
            print("  ✅ Generated `jwt_private_key` and `jwt_public_key`.")
        except Exception as e:
            print(f"  ❌ Error generating JWT keys: {e}")
    else:
        print("✅ `auth.jwt_private_key` and `auth.jwt_public_key` are specified.")

    if needs_update:
        print("  ✅ `settings.yaml` has been updated with auth settings.")


def check_and_prompt_api_jwt_token():
    """
    Check if `accounts.api_jwt_token` is set in `settings.yaml`.
    Prompt the user to set it if it is missing, allow them to input it,
    and open the required URL in the default web browser.
    """
    import webbrowser

    ACCOUNTS_TOKEN_URL = (
        "https://api.innohassle.ru/accounts/v0/tokens/"
        "generate-service-token?sub=local-dev&scopes=users&only_for_me=true"
    )
    settings = get_settings()
    accounts = settings.get("accounts", {})
    api_jwt_token = accounts.get("api_jwt_token")

    if not api_jwt_token or api_jwt_token == "...":
        print("⚠️ `accounts.api_jwt_token` is missing in `settings.yaml`.")
        print(f"  ➡️ Opening the following URL to generate a token:\n  {ACCOUNTS_TOKEN_URL}")

        webbrowser.open(ACCOUNTS_TOKEN_URL)

        token = input("  🔑 Please paste the generated token below (or press Enter to skip):\n  > ").strip()

        if token:
            try:
                with open(SETTINGS_FILE) as f:
                    as_text = f.read()
                as_text = as_text.replace("api_jwt_token: null", f"api_jwt_token: {token}")
                as_text = as_text.replace("api_jwt_token: ...", f"api_jwt_token: {token}")
                with open(SETTINGS_FILE, "w") as f:
                    f.write(as_text)
                print("  ✅ `accounts.api_jwt_token` has been updated in `settings.yaml`.")
            except Exception as e:
                print(f"  ❌ Error updating `settings.yaml`: {e}")
        else:
            print("  ⚠️ Token was not provided. Please manually update `settings.yaml` later.")
            print(f"  ➡️ Refer to the URL: {ACCOUNTS_TOKEN_URL}")
    else:
        print("✅ `accounts.api_jwt_token` is specified.")


def prepare():
    ensure_settings_file()
    ensure_pre_commit_hooks()
    ensure_auth_settings()
    check_database_access()
    check_and_prompt_api_jwt_token()
