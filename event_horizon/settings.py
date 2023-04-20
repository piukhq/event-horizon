import sys

from decouple import Choices, config
from redis import Redis

from event_horizon.key_vault import KeyVault


def check_testing(value: bool) -> bool:
    command = sys.argv[0]
    if command == "poetry":
        command = sys.argv[2] if len(sys.argv) > 2 else "None"

    if "test" in command:
        return True

    return value


FLASK_ADMIN_SWATCH: str = config("EVENT_HORIZON_THEME", "simplex")
TESTING: bool = check_testing(config("TESTING", default=False, cast=bool))

KEY_VAULT_URI: str = config("KEY_VAULT_URI", "https://uksouth-dev-2p5g.vault.azure.net/")
key_vault = KeyVault(KEY_VAULT_URI)

SECRET_KEY: str = config("SECRET_KEY", default=None) or key_vault.get_secret("bpl-event-horizon-secret-key")

ROUTE_BASE = "/admin"

PROJECT_NAME = "event-horizon"

# AAD SSO
OAUTH_REDIRECT_URI: str = config("OAUTH_REDIRECT_URI", default=None)
AZURE_TENANT_ID: str = config("AZURE_TENANT_ID", "a6e2367a-92ea-4e5a-b565-723830bcc095")
OAUTH_SERVER_METADATA_URL = f"https://login.microsoftonline.com/{AZURE_TENANT_ID}/v2.0/.well-known/openid-configuration"
EVENT_HORIZON_CLIENT_ID: str = config("EVENT_HORIZON_CLIENT_ID", default=None)
EVENT_HORIZON_CLIENT_SECRET: str = config("EVENT_HORIZON_CLIENT_SECRET", default=None) or key_vault.get_secret(
    "bpl-event-horizon-sso-client-secret"
)

DEV_PORT: int = config("DEV_PORT", "5000", cast=int)
DEBUG: bool = config("DEBUG", "False", cast=bool)
DATABASE_URI: str = config("DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/{}")
POLARIS_DATABASE_URI = DATABASE_URI.format(config("POLARIS_DATABASE_NAME", "polaris"))
VELA_DATABASE_URI = DATABASE_URI.format(config("VELA_DATABASE_NAME", "vela"))
CARINA_DATABASE_URI = DATABASE_URI.format(config("CARINA_DATABASE_NAME", "carina"))
HUBBLE_DATABASE_URI = DATABASE_URI.format(config("HUBBLE_DATABASE_NAME", "hubble"))
SENTRY_DSN: str = config("SENTRY_DSN", default=None)
SENTRY_ENV: str = config("SENTRY_ENV", default=None)
REDIS_URL: str = config("REDIS_URL", "redis://localhost:6379/0")
QUERY_LOG_LEVEL: str = config(
    "QUERY_LOG_LEVEL", "WARN", cast=Choices(["CRITICAL", "ERROR", "WARNING", "WARN", "INFO", "DEBUG"])
)

POLARIS_ENDPOINT_PREFIX = "polaris"
VELA_ENDPOINT_PREFIX = "vela"
CARINA_ENDPOINT_PREFIX = "carina"
HUBBLE_ENDPOINT_PREFIX = "hubble"

POLARIS_HOST: str = config("POLARIS_HOST", "http://polaris-api")
POLARIS_BASE_URL: str = config("POLARIS_BASE_URL", f"{POLARIS_HOST}/loyalty")
POLARIS_AUTH_TOKEN: str = config("POLARIS_AUTH_TOKEN", default=None) or key_vault.get_secret(
    "bpl-polaris-api-auth-token"
)

CARINA_HOST: str = config("CARINA_HOST", "http://carina-api")
CARINA_BASE_URL: str = config("CARINA_BASE_URL", f"{CARINA_HOST}/rewards")
CARINA_AUTH_TOKEN: str = config("CARINA_AUTH_TOKEN", default=None) or key_vault.get_secret("bpl-carina-api-auth-token")

VELA_HOST: str = config("VELA_HOST", "http://vela-api")
VELA_BASE_URL: str = config("VELA_BASE_URL", f"{VELA_HOST}/retailers")
VELA_AUTH_TOKEN: str = config("VELA_AUTH_TOKEN", default=None) or key_vault.get_secret("bpl-vela-api-auth-token")
REQUEST_TIMEOUT: int = config("REQUEST_TIMEOUT", 2, cast=int)

RABBITMQ_DSN: str = config("RABBITMQ_DSN", "amqp://guest:guest@localhost:5672//")
MESSAGE_EXCHANGE_NAME: str = config("MESSAGE_EXCHANGE_NAME", "hubble-activities")


redis = Redis.from_url(
    REDIS_URL,
    socket_connect_timeout=3,
    socket_keepalive=True,
    retry_on_timeout=False,
)
