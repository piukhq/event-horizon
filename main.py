from datetime import datetime

from flask import Flask, session
from flask_admin import Admin, expose, AdminIndexView
from flask_admin.contrib.sqla import ModelView

import settings
from azure_sso import AzureSSO
from db import load_session, User, MembershipCard, Voucher

app = Flask(__name__)
db_session = load_session()
app.config.from_object(settings)
sso = AzureSSO(app)

# set optional bootswatch theme
app.config["FLASK_ADMIN_SWATCH"] = "cerulean"


class AuthorisedModelView(ModelView):

    def is_accessible(self):
        try:
            is_not_expired = session["user"]["exp"] >= datetime.utcnow().timestamp()
            allowed_roles = set(session["user"]["roles"]).issubset({"Admin", "Editor"})

            return is_not_expired and allowed_roles
        except KeyError:
            return False


class MyAdminIndexView(AdminIndexView):

    @expose('/')
    @sso.login_required()
    def index(self):
        return super(MyAdminIndexView, self).index()


admin = Admin(app, name="test flask admin", template_mode="bootstrap3", index_view=MyAdminIndexView())

# Add administrative views here
admin.add_view(AuthorisedModelView(User, db_session))
admin.add_view(AuthorisedModelView(MembershipCard, db_session))
admin.add_view(AuthorisedModelView(Voucher, db_session))

app.run()
