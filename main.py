from flask import Flask
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_azure_oauth import FlaskAzureOauth

from db import load_session, User, MembershipCard, Voucher

app = Flask(__name__)
session = load_session()

# set optional bootswatch theme
app.config["FLASK_ADMIN_SWATCH"] = "cerulean"
app.config['AZURE_OAUTH_TENANCY'] = 'a6e2367a-92ea-4e5a-b565-723830bcc095'
app.config['AZURE_OAUTH_APPLICATION_ID'] = '4fd277c2-7542-47d4-b4d7-6943c31b0ce3'

admin = Admin(app, name="test flask admin", template_mode="bootstrap3")
auth = FlaskAzureOauth()
auth.init_app(app)


class AuthorisedModelView(ModelView):

    # @auth()
    def is_accessible(self):
        return True


# Add administrative views here
admin.add_view(AuthorisedModelView(User, session))
admin.add_view(AuthorisedModelView(MembershipCard, session))
admin.add_view(AuthorisedModelView(Voucher, session))

app.run()
