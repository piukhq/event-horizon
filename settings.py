from os import getenv

from dotenv import load_dotenv

load_dotenv()

FLASK_ADMIN_SWATCH = "cerulean"
SECRET_KEY = "476dd64f-0a46-47e4-b094-8e2743ebe678"
SESSION_TYPE = "filesystem"

BPL_CLIENT_SECRET = "EMq_4c.h8Pim7.ibmb2-.xxB1n6l-o2wj_"
BPL_CLIENT_ID = "2043ed95-8a99-45c9-93b5-71317a50a3ee"
TENANT_ID = "a6e2367a-92ea-4e5a-b565-723830bcc095"
OAUTH_SERVER_METADATA_URL = f"https://login.microsoftonline.com/{TENANT_ID}/v2.0/.well-known/openid-configuration"

DEV_PORT = int(getenv("DEV_PORT", "5000"))
SQLALCHEMY_DATABASE_URI = getenv(
    "SQLALCHEMY_DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/test_fastapi"
)
