from flask_admin import Admin
from flask_admin.model.form import InlineFormAdmin
from wtforms.validators import DataRequired

from app.admin.validators import validate_retailer_config
from app.db import AccountHolder, AccountHolderProfile, Retailer, SessionMaker

from .classes import AuthorisedModelView, MyAdminIndexView

admin = Admin(name="Polaris Admin", template_mode="bootstrap3", index_view=MyAdminIndexView())


class AccountHolderProfileForm(InlineFormAdmin):
    form_label = "Profile"


class AccountHolderAdmin(AuthorisedModelView):
    inline_models = (AccountHolderProfileForm(AccountHolderProfile),)
    form_widget_args = {"created_at": {"disabled": True}}


class RetailerAdmin(AuthorisedModelView):
    form_create_rules = ("name", "slug", "card_number_prefix", "config")
    form_excluded_columns = ("account_holder_collection",)
    form_widget_args = {
        "created_at": {"disabled": True},
        "card_number_length": {"disabled": True},
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
            "validators": [DataRequired(message="Configuration is required"), validate_retailer_config],
            "render_kw": {"placeholder": config_placeholder},
            "description": "Configuration in YAML format",
        },
        "name": {"validators": [DataRequired(message="Name is required")]},
        "slug": {"validators": [DataRequired(message="Slug is required")]},
        "card_number_prefix": {"validators": [DataRequired("Card number prefix is required")]},
    }


with SessionMaker() as db_session:
    admin.add_view(AccountHolderAdmin(AccountHolder, db_session, "Account Holders"))
    admin.add_view(RetailerAdmin(Retailer, db_session, "Retailers"))
