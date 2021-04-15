from datetime import datetime
from typing import TYPE_CHECKING, Optional

from flask import Markup, redirect, session, url_for
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
    can_delete = False

    def is_accessible(self) -> bool:
        try:
            is_not_expired = session["user"]["exp"] >= datetime.utcnow().timestamp()
            if not is_not_expired:
                del session["user"]
                return False

            user_roles = set(session["user"]["roles"])
            valid_user_roles = user_roles.intersection(self.ALL_AZURE_ROLES)
            self.can_create = self.can_edit = bool(user_roles.intersection(self.RW_AZURE_ROLES))
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
    name="Polaris Admin", template_mode="bootstrap4", index_view=PolarisAdminIndexView(url="/bpl/admin/")
)


class AccountHolderProfileForm(InlineFormAdmin):
    form_label = "Profile"


class AccountHolderAdmin(AuthorisedModelView):
    column_display_pk = True
    column_filters = ("retailer.slug", "retailer.name", "retailer.id", "status")
    column_searchable_list = ("email", "id")
    inline_models = (AccountHolderProfileForm(AccountHolderProfile),)
    form_widget_args = {"created_at": {"disabled": True}}
    column_formatters = dict(
        retailer=lambda v, c, model, p: Markup("<pre>")
        + Markup.escape(model.retailer.name)
        + Markup("<br />(")
        + Markup.escape(model.retailer.slug)
        + Markup(") </pre>")
    )


class AccountHolderProfileAdmin(AuthorisedModelView):
    column_searchable_list = ("accountholder.id", "accountholder.email")
    column_labels = dict(accountholder="Account Holder")
    column_formatters = dict(
        accountholder=lambda v, c, model, p: Markup.escape(model.accountholder.email)
        + Markup("<br />" + f"({model.accountholder.id})")
    )


class RetailerAdmin(AuthorisedModelView):
    column_filters = ("created_at",)
    column_searchable_list = ("id", "slug", "name")
    column_exclude_list = ("config",)
    form_create_rules = ("name", "slug", "account_number_prefix", "config")
    form_excluded_columns = ("account_holder_collection",)
    form_widget_args = {
        "created_at": {"disabled": True},
        "account_number_length": {"disabled": True},
        "config": {"rows": 20},
    }
    form_edit_rules = ("name", "config")

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
    column_formatters = dict(
        config=lambda v, c, model, p: Markup("<pre>") + Markup.escape(model.config) + Markup("</pre>")
    )


with SessionMaker() as db_session:
    polaris_admin.add_view(AccountHolderAdmin(AccountHolder, db_session, "Account Holders", endpoint="account-holders"))
    polaris_admin.add_view(AccountHolderProfileAdmin(AccountHolderProfile, db_session, "Profiles", endpoint="profiles"))
    polaris_admin.add_view(RetailerAdmin(Retailer, db_session, "Retailers", endpoint="retailers"))
