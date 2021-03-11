from datetime import datetime
from typing import TYPE_CHECKING, Optional

from flask import session, redirect, url_for
from flask_admin import AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView

if TYPE_CHECKING:
    from werkzeug.wrappers import Response


# custom admin classes needed for authorisation
class AuthorisedModelView(ModelView):
    def is_accessible(self) -> bool:
        try:
            is_not_expired = session["user"]["exp"] >= datetime.utcnow().timestamp()
            allowed_roles = set(session["user"]["roles"]).issubset({"Admin", "Editor"})

            return is_not_expired and allowed_roles
        except KeyError:
            return False

    def inaccessible_callback(self, name: str, **kwargs: Optional[dict]) -> "Response":
        return redirect(url_for("auth_views.login"))


class MyAdminIndexView(AdminIndexView):
    @expose("/")
    def index(self) -> "Response":
        if "user" not in session:
            return redirect("/login")
        return super(MyAdminIndexView, self).index()
