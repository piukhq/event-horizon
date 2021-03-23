from typing import TYPE_CHECKING

from authlib.integrations.flask_client import OAuth
from flask import url_for, session, redirect, Blueprint

from settings import OAUTH_SERVER_METADATA_URL

if TYPE_CHECKING:
    from werkzeug.wrappers import Response

auth_bp = Blueprint("auth_views", __name__)

oauth = OAuth()
oauth.register(
    "bpl",
    server_metadata_url=OAUTH_SERVER_METADATA_URL,
    client_kwargs={"scope": "openid profile email"},
)


@auth_bp.route("/login")
def login() -> "Response":
    redirect_uri = url_for("auth_views.authorize", _external=True)
    return oauth.bpl.authorize_redirect(redirect_uri)


@auth_bp.route("/logout")
def logout() -> "Response":
    # session['user'] will always be set again as long
    # as your AAD session is still alive.
    session.pop("user", None)
    return redirect("/admin")


@auth_bp.route("/admin/callback")
def authorize() -> "Response":
    token = oauth.bpl.authorize_access_token()
    userinfo = oauth.bpl.parse_id_token(token)
    session["user"] = userinfo
    return redirect("/admin")
