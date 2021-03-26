from flask_admin import Admin
from flask_admin.model.form import InlineFormAdmin
from wtforms.validators import DataRequired

from app.polaris.db import AccountHolder, AccountHolderProfile, Retailer, SessionMaker
from app.polaris.validators import validate_retailer_config
from app.polaris.views.admin import AuthorisedModelView, PolarisAdminIndexView

polaris_admin = Admin(name="Polaris Admin", template_mode="bootstrap3", index_view=PolarisAdminIndexView())


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
