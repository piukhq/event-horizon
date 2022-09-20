import sys

from os import getenv
from typing import Any, Callable

from dotenv import load_dotenv
from redis import Redis

from app.key_vault import KeyVault

load_dotenv()


def get_env(k: str, default: str = None, *, conv: Callable = str) -> Any:
    v = getenv(k, default)
    if v is not None:
        return conv(v)

    return None


def to_bool(v: str) -> bool:
    value = v.lower()

    if value not in ["true", "false"]:
        raise ValueError("Invalid value for a boolean.")

    return value == "true"


def is_test(v: str) -> bool:
    command = sys.argv[0]
    args = sys.argv[1:] if len(sys.argv) > 1 else []

    if "pytest" in command or any("test" in arg for arg in args):
        return True

    return to_bool(v)


FLASK_ADMIN_SWATCH = get_env("EVENT_HORIZON_THEME", "simplex")
TESTING = get_env("TESTING", "False", conv=is_test)

KEY_VAULT_URI = get_env("KEY_VAULT_URI", "https://bink-uksouth-dev-com.vault.azure.net/")
key_vault = KeyVault(KEY_VAULT_URI)

SECRET_KEY = get_env("SECRET_KEY") or key_vault.get_secret("bpl-event-horizon-secret-key")

ROUTE_BASE = "/admin"

PROJECT_NAME = "event-horizon"

# AAD SSO
OAUTH_REDIRECT_URI = get_env("OAUTH_REDIRECT_URI")
AZURE_TENANT_ID = get_env("AZURE_TENANT_ID", "a6e2367a-92ea-4e5a-b565-723830bcc095")
OAUTH_SERVER_METADATA_URL = f"https://login.microsoftonline.com/{AZURE_TENANT_ID}/v2.0/.well-known/openid-configuration"
EVENT_HORIZON_CLIENT_ID = get_env("EVENT_HORIZON_CLIENT_ID")
EVENT_HORIZON_CLIENT_SECRET = get_env("EVENT_HORIZON_CLIENT_SECRET") or key_vault.get_secret(
    "bpl-event-horizon-sso-client-secret"
)

DEV_PORT = get_env("DEV_PORT", "5000", conv=int)
DEBUG = get_env("DEBUG", "False", conv=to_bool)
DATABASE_URI = get_env("DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/{}")
POLARIS_DATABASE_URI = DATABASE_URI.format(get_env("POLARIS_DATABASE_NAME", "polaris"))
VELA_DATABASE_URI = DATABASE_URI.format(get_env("VELA_DATABASE_NAME", "vela"))
CARINA_DATABASE_URI = DATABASE_URI.format(get_env("CARINA_DATABASE_NAME", "carina"))
HUBBLE_DATABASE_URI = DATABASE_URI.format(get_env("HUBBLE_DATABASE_NAME", "hubble"))
SENTRY_DSN = get_env("SENTRY_DSN")
SENTRY_ENV = get_env("SENTRY_ENV")
REDIS_URL = get_env("REDIS_URL", "redis://localhost:6379/0")
QUERY_LOG_LEVEL = get_env("QUERY_LOG_LEVEL", "WARN")

POLARIS_ENDPOINT_PREFIX = "polaris"
VELA_ENDPOINT_PREFIX = "vela"
CARINA_ENDPOINT_PREFIX = "carina"
HUBBLE_ENDPOINT_PREFIX = "hubble"

POLARIS_HOST = getenv("POLARIS_HOST", "http://polaris-api")
POLARIS_BASE_URL = getenv("POLARIS_BASE_URL", f"{POLARIS_HOST}/loyalty")
POLARIS_AUTH_TOKEN = get_env("POLARIS_AUTH_TOKEN") or key_vault.get_secret("bpl-polaris-api-auth-token")

VELA_HOST = getenv("VELA_HOST", "http://vela-api")
VELA_BASE_URL = getenv("VELA_BASE_URL", f"{VELA_HOST}/retailers")
VELA_AUTH_TOKEN = get_env("VELA_AUTH_TOKEN") or key_vault.get_secret("bpl-vela-api-auth-token")
REQUEST_TIMEOUT = 2

RABBITMQ_DSN: str = "amqp://guest:guest@localhost:5672//"
MESSAGE_EXCHANGE_NAME: str = "hubble-activities"


redis = Redis.from_url(
    REDIS_URL,
    socket_connect_timeout=3,
    socket_keepalive=True,
    retry_on_timeout=False,
)
