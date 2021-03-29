from typing import TYPE_CHECKING

from flask import Blueprint, redirect, session, url_for

from app.app import oauth

if TYPE_CHECKING:
    from werkzeug.wrappers import Response

auth_bp = Blueprint("auth_views", __name__)


@auth_bp.route("/login")
def login() -> "Response":
    redirect_uri = url_for("auth_views.authorize", _external=True)
    return oauth.event_horizon.authorize_redirect(redirect_uri)


@auth_bp.route("/logout")
def logout() -> "Response":
    # session['user'] will always be set again as long
    # as your AAD session is still alive.
    session.pop("user", None)
    return redirect("/admin")


@auth_bp.route("/admin/callback")
def authorize() -> "Response":
    token = oauth.event_horizon.authorize_access_token()
    userinfo = oauth.event_horizon.parse_id_token(token)
    session["user"] = userinfo
    return redirect("/admin")
