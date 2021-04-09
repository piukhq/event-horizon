from os import getenv

from dotenv import load_dotenv

from app.key_vault import KeyVault

load_dotenv()
FLASK_ADMIN_SWATCH = "simplex"

KEY_VAULT_URI = getenv("KEY_VAULT_URI", "https://bink-uksouth-dev-com.vault.azure.net/")
key_vault = KeyVault(KEY_VAULT_URI)

SECRET_KEY = getenv("SECRET_KEY") or key_vault.get_secret("bpl-event-horizon-secret-key")

# AAD SSO
OAUTH_REDIRECT_URI = getenv("OAUTH_REDIRECT_URI")
AZURE_TENANT_ID = getenv("AZURE_TENANT_ID", "a6e2367a-92ea-4e5a-b565-723830bcc095")
OAUTH_SERVER_METADATA_URL = f"https://login.microsoftonline.com/{AZURE_TENANT_ID}/v2.0/.well-known/openid-configuration"
EVENT_HORIZON_CLIENT_ID = getenv("EVENT_HORIZON_CLIENT_ID")
EVENT_HORIZON_CLIENT_SECRET = getenv("EVENT_HORIZON_CLIENT_SECRET") or key_vault.get_secret(
    "bpl-event-horizon-sso-client-secret"
)

DEV_PORT = int(getenv("DEV_PORT", "5000"))
SQLALCHEMY_DATABASE_URI = getenv("SQLALCHEMY_DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/polaris")
