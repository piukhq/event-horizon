from datetime import datetime
from typing import TYPE_CHECKING, Optional

from flask import abort, redirect, session, url_for
from flask_admin.contrib.sqla import ModelView

if TYPE_CHECKING:
    from werkzeug.wrappers import Response  # pragma: no cover


class UserSessionMixin:
    RO_AZURE_ROLES = {"Viewer"}
    RW_AZURE_ROLES = {"Admin", "Editor"}
    ALL_AZURE_ROLES = RW_AZURE_ROLES | RO_AZURE_ROLES

    @property
    def user_info(self) -> dict:
        return session.get("user", {})

    @property
    def user_session_expired(self) -> bool:
        session_exp: Optional[int] = self.user_info.get("exp")
        return session_exp < datetime.utcnow().timestamp() if session_exp else True

    @property
    def user_roles(self) -> set[str]:
        return set(self.user_info.get("roles", []))

    @property
    def user_is_authorized(self) -> bool:
        return bool(self.user_roles.intersection(self.ALL_AZURE_ROLES))


# custom admin classes needed for authorisation
class AuthorisedModelView(ModelView, UserSessionMixin):
    can_view_details = True
    can_delete = False

    def is_accessible(self) -> bool:
        if not self.user_info:
            return False
        self.can_create = self.can_edit = bool(self.user_roles.intersection(self.RW_AZURE_ROLES))
        return not self.user_session_expired and self.user_is_authorized

    def inaccessible_callback(self, name: str, **kwargs: Optional[dict]) -> "Response":
        if self.user_info and not self.user_is_authorized:
            return abort(403)
        session.pop("user", None)
        return redirect(url_for("auth_views.login"))
