from datetime import datetime
from typing import TYPE_CHECKING, Optional

from flask import redirect, session, url_for
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.model.form import InlineFormAdmin
from wtforms.validators import DataRequired

from app.polaris.db import AccountHolder, AccountHolderProfile, Retailer, SessionMaker
from app.polaris.validators import validate_retailer_config

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


class PolarisAdminIndexView(AdminIndexView):
    @expose("/")
    def index(self) -> "Response":
        if "user" not in session:
            return redirect(url_for("auth_views.login"))
        return super(PolarisAdminIndexView, self).index()


polaris_admin = Admin(
    name="Polaris Admin", template_mode="bootstrap3", index_view=PolarisAdminIndexView(url="/bpl/admin/")
)


class AccountHolderProfileForm(InlineFormAdmin):
    form_label = "Profile"


class AccountHolderAdmin(AuthorisedModelView):
    inline_models = (AccountHolderProfileForm(AccountHolderProfile),)
    form_widget_args = {"created_at": {"disabled": True}}


class RetailerAdmin(AuthorisedModelView):
    form_create_rules = ("name", "slug", "account_number_prefix", "config")
    form_excluded_columns = ("account_holder_collection",)
    form_widget_args = {
        "created_at": {"disabled": True},
        "account_number_length": {"disabled": True},
        "config": {"rows": 20},
    }

    config_placeholder = """
email:
    required: true
    label: Email address
first_name:
    required: true
    label: Forename
last_name:
    required: true
    label: Surname
""".strip()

    form_args = {
        "config": {
            "label": "Profile Field Configuration",
            "validators": [
                DataRequired(message="Configuration is required"),
                validate_retailer_config,
            ],
            "render_kw": {"placeholder": config_placeholder},
            "description": "Configuration in YAML format",
        },
        "name": {"validators": [DataRequired(message="Name is required")]},
        "slug": {"validators": [DataRequired(message="Slug is required")]},
        "account_number_prefix": {"validators": [DataRequired("Account number prefix is required")]},
    }


with SessionMaker() as db_session:
    polaris_admin.add_view(AccountHolderAdmin(AccountHolder, db_session, "Account Holders"))
    polaris_admin.add_view(RetailerAdmin(Retailer, db_session, "Retailers"))
