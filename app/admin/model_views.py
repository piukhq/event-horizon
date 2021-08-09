from datetime import datetime
from typing import TYPE_CHECKING, List, Optional, Tuple, Union

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
    can_edit = True  # Flask admin's usual default for can_edit
    can_create = True  # Flask admin's usual default for can_create
    can_delete = False

    def is_accessible(self) -> bool:
        if not self.user_info:
            return False
        self.can_create = self.can_create and bool(self.user_roles.intersection(self.RW_AZURE_ROLES))
        self.can_edit = self.can_edit and bool(self.user_roles.intersection(self.RW_AZURE_ROLES))
        return not self.user_session_expired and self.user_is_authorized

    def inaccessible_callback(self, name: str, **kwargs: Optional[dict]) -> "Response":
        if self.user_info and not self.user_is_authorized:
            return abort(403)
        session.pop("user", None)
        return redirect(url_for("auth_views.login"))


class BaseModelView(AuthorisedModelView):
    """
    Set some baseline behaviour for all ModelViews
    """

    list_template = "eh_list.html"
    edit_template = "eh_edit.html"
    create_template = "eh_create.html"
    column_default_sort: Union[str, Tuple[str, bool]] = ("created_at", True)
    form_excluded_columns: Tuple[str, ...] = ("created_at", "updated_at")

    def get_list_columns(self) -> List[str]:
        # Shunt created_at and updated_at to the end of the table
        list_columns = super().get_list_columns()
        for name in ("created_at", "updated_at"):
            for i, (col_name, _disp_name) in enumerate(list_columns):
                if col_name == name:
                    list_columns += [list_columns.pop(i)]
                    break
        return list_columns
