from typing import TYPE_CHECKING

from flask import redirect, session, url_for
from flask_admin import AdminIndexView, expose

if TYPE_CHECKING:
    from werkzeug.wrappers import Response


class EventHorizonAdminIndexView(AdminIndexView):
    @expose("/")
    def index(self) -> "Response":
        if "user" not in session:
            return redirect(url_for("auth_views.login"))
        return super(EventHorizonAdminIndexView, self).index()
