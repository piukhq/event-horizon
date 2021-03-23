from flask_admin import Admin
from flask_admin.model.form import InlineFormAdmin

from app.admin.validators import validate_retailer_config
from app.db import AccountHolder, AccountHolderProfile, Retailer, SessionMaker
from .classes import MyAdminIndexView, AuthorisedModelView

admin = Admin(name="Polaris Admin", template_mode="bootstrap3", index_view=MyAdminIndexView())


class AccountHolderProfileForm(InlineFormAdmin):
    form_label = "Profile"


class AccountHolderAdmin(AuthorisedModelView):
    inline_models = (AccountHolderProfileForm(AccountHolderProfile),)
    form_widget_args = {"created_at": {"disabled": True}}


class RetailerAdmin(AuthorisedModelView):
    form_create_rules = ("name", "slug", "card_number_prefix")
    form_excluded_columns = ("accountholder_collection",)
    form_widget_args = {
        "created_at": {"disabled": True},
        "card_number_length": {"disabled": True},
        "profile_config": {"rows": 20},
    }
    form_args = {"profile_config": {"validators": [validate_retailer_config]}}


with SessionMaker() as db_session:
    admin.add_view(AccountHolderAdmin(AccountHolder, db_session, "Account Holders"))
    admin.add_view(RetailerAdmin(Retailer, db_session, "Retailers"))
