from typing import TYPE_CHECKING

from authlib.integrations.base_client.errors import MismatchingStateError
from flask import Blueprint, redirect, session, url_for

from app.app import oauth
from app.settings import OAUTH_REDIRECT_URI, ROUTE_BASE

if TYPE_CHECKING:
    from werkzeug.wrappers import Response

auth_bp = Blueprint("auth_views", __name__, url_prefix=ROUTE_BASE)


@auth_bp.route("/login/")
def login() -> "Response":
    if OAUTH_REDIRECT_URI:
        redirect_uri = OAUTH_REDIRECT_URI
    else:
        redirect_uri = url_for("auth_views.authorize", _external=True)

    return oauth.event_horizon.authorize_redirect(redirect_uri)


@auth_bp.route("/logout/")
def logout() -> "Response":
    # session['user'] will always be set again as long
    # as your AAD session is still alive.
    session.pop("user", None)
    return redirect(url_for("admin.index"))


@auth_bp.route("/authorize/")
def authorize() -> "Response":
    try:
        token = oauth.event_horizon.authorize_access_token()
    except MismatchingStateError:
        return redirect(url_for("auth_views.login"))
    userinfo = oauth.event_horizon.parse_id_token(token, None)
    session["user"] = userinfo
    return redirect(url_for("admin.index"))
