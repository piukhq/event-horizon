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
    else:
        return None


def to_bool(v: str) -> bool:
    if v.lower() == "true":
        return True
    else:
        return False


FLASK_ADMIN_SWATCH = "simplex"

KEY_VAULT_URI = get_env("KEY_VAULT_URI", "https://bink-uksouth-dev-com.vault.azure.net/")
key_vault = KeyVault(KEY_VAULT_URI)

SECRET_KEY = get_env("SECRET_KEY") or key_vault.get_secret("bpl-event-horizon-secret-key")


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
POLARIS_DATABASE_URI = get_env("POLARIS_DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/polaris")
VELA_DATABASE_URI = get_env("VELA_DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/vela")
CARINA_DATABASE_URI = get_env("CARINA_DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/carina")
SENTRY_DSN = get_env("SENTRY_DSN")
SENTRY_ENV = get_env("SENTRY_ENV")
ACCOUNT_HOLDER_ACTIVATION_TASK_QUEUE = get_env("ACCOUNT_HOLDER_ACTIVATION_TASK_QUEUE", "bpl_account_holder_activations")
REDIS_URL = get_env("REDIS_URL", "redis://localhost:6379/0")

redis = Redis.from_url(
    REDIS_URL,
    socket_connect_timeout=3,
    socket_keepalive=True,
    retry_on_timeout=False,
)
