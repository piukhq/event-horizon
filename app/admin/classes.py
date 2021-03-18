from datetime import datetime
from typing import TYPE_CHECKING, Optional

from flask import session, redirect, url_for
from flask_admin import AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView

if TYPE_CHECKING:
    from werkzeug.wrappers import Response


# custom admin classes needed for authorisation
class AuthorisedModelView(ModelView):
    RO_AZURE_ROLES = {"Viewer"}
    RW_AZURE_ROLES = {"Admin", "Editor"}
    ALL_AZURE_ROLES = RW_AZURE_ROLES | RO_AZURE_ROLES
    can_view_details = True

    def is_accessible(self) -> bool:
        try:
            is_not_expired = session["user"]["exp"] >= datetime.utcnow().timestamp()
            if not is_not_expired:
                del session["user"]
                return False

            user_roles = set(session["user"]["roles"])
            valid_user_roles = user_roles.intersection(self.ALL_AZURE_ROLES)
            self.can_create = self.can_edit = self.can_delete = bool(user_roles.intersection(self.RW_AZURE_ROLES))
            return is_not_expired and bool(valid_user_roles)
        except KeyError:
            return False

    def inaccessible_callback(self, name: str, **kwargs: Optional[dict]) -> "Response":
        try:
            if session["user"]["exp"] < datetime.utcnow().timestamp():
                del session["user"]
        except KeyError:
            pass

        return redirect(url_for("auth_views.login"))


class MyAdminIndexView(AdminIndexView):
    @expose("/")
    def index(self) -> "Response":
        if "user" not in session:
            return redirect("/login")
        return super(MyAdminIndexView, self).index()
