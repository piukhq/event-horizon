from flask_admin import Admin
from flask_admin.model.form import InlineFormAdmin

from app.db import AccountHolder, AccountHolderProfile, Retailer, SessionMaker
from .classes import MyAdminIndexView, AuthorisedModelView

admin = Admin(
    name="Polaris Admin", template_mode="bootstrap3", index_view=MyAdminIndexView()
)


class AccountHolderProfileForm(InlineFormAdmin):
    form_label = "Profile"


class AccountHolderAdmin(AuthorisedModelView):
    inline_models = (AccountHolderProfileForm(AccountHolderProfile),)
    form_widget_args = {"created_at": {"disabled": True}}


class RetailerAdmin(AuthorisedModelView):
    form_create_rules = ("name", "slug", "card_number_prefix")
    form_excluded_columns = ("account_holder_collection",)
    form_widget_args = {"created_at": {"disabled": True}, "card_number_length": {"disabled": True}}


with SessionMaker() as db_session:
    admin.add_view(AccountHolderAdmin(AccountHolder, db_session))
    admin.add_view(RetailerAdmin(Retailer, db_session))
