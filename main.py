from datetime import datetime

from flask import Flask, session, url_for, redirect
from flask_admin import Admin, expose, AdminIndexView
from flask_admin.contrib.sqla import ModelView

import settings
from authlib.integrations.flask_client import OAuth
from db import load_session, User, MembershipCard, Voucher

app = Flask(__name__)
db_session = load_session()
app.config.from_object(settings)

oauth = OAuth(app)
oauth.register(
    'bpl',
    server_metadata_url=settings.OAUTH_SERVER_METADATA_URL,
    client_kwargs={'scope': 'openid profile email'}
)
# set optional bootswatch theme
app.config["FLASK_ADMIN_SWATCH"] = "cerulean"

@app.route('/login')
def login():
    redirect_uri = url_for('authorize', _external=True)
    return oauth.bpl.authorize_redirect(redirect_uri)


@app.route('/logout')
def logout():
    # session['user'] will always be set again as long
    # as your AAD session is still alive.
    session.pop('user', None)
    return redirect('/admin')


@app.route('/admin/callback')
def authorize():
    token = oauth.bpl.authorize_access_token()
    userinfo = oauth.bpl.parse_id_token(token)
    session["user"] = userinfo
    return redirect('/admin')


class AuthorisedModelView(ModelView):
    def is_accessible(self):
        try:
            is_not_expired = session["user"]["exp"] >= datetime.utcnow().timestamp()
            allowed_roles = set(session["user"]["roles"]).issubset({"Admin", "Editor"})

            return is_not_expired and allowed_roles
        except KeyError:
            return False

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login'))


class MyAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        if 'user' not in session:
            return redirect('/login')
        return super(MyAdminIndexView, self).index()


admin = Admin(app, name="test flask admin", template_mode="bootstrap3", index_view=MyAdminIndexView())

# Add administrative views here
admin.add_view(AuthorisedModelView(User, db_session))
admin.add_view(AuthorisedModelView(MembershipCard, db_session))
admin.add_view(AuthorisedModelView(Voucher, db_session))

app.run()
