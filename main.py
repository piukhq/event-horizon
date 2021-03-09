from azure_oidc import OIDCConfig
from azure_oidc.auth import AzureADAuth
from flask import Flask, request
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

from models import load_session, User, MembershipCard

tenant_id = "a6e2367a-92ea-4e5a-b565-723830bcc095"  # Directory (tenant) ID goes here
config = OIDCConfig(
    base_url=f"https://login.microsoftonline.com/{tenant_id}/v2.0",
    issuer=f"https://sts.windows.net/{tenant_id}/",
    audience="4fd277c2-7542-47d4-b4d7-6943c31b0ce3"  # Application ID URI goes here
)

authenticator = AzureADAuth(config)
app = Flask(__name__)
session = load_session()

# set optional bootswatch theme
app.config["FLASK_ADMIN_SWATCH"] = "cerulean"

admin = Admin(app, name="test flask admin", template_mode="bootstrap3")


class AuthorisedModelView(ModelView):

    def is_accessible(self):
        authorization_header = request.headers.get('Authorization')
        return authenticator.authenticate(authorization_header, auth_scopes=["admin"])


# Add administrative views here
admin.add_view(AuthorisedModelView(User, session))
admin.add_view(AuthorisedModelView(MembershipCard, session))

app.run()
