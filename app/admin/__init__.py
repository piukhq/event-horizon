from flask_admin import Admin
from flask_admin.model.form import InlineFormAdmin

from app.db import User, UserProfile, Merchant, SessionMaker
from .classes import MyAdminIndexView, AuthorisedModelView

admin = Admin(
    name="Polaris Admin", template_mode="bootstrap3", index_view=MyAdminIndexView()
)


class UserProfileForm(InlineFormAdmin):
    form_label = "Profile"


class UserAdmin(AuthorisedModelView):
    inline_models = (UserProfileForm(UserProfile),)
    form_widget_args = {"created_at": {"disabled": True}}


class MerchantAdmin(AuthorisedModelView):
    form_create_rules = ("name", "slug", "card_number_prefix")
    form_excluded_columns = ("user_collection",)
    form_widget_args = {"created_at": {"disabled": True}, "card_number_length": {"disabled": True}}


with SessionMaker() as db_session:
    admin.add_view(UserAdmin(User, db_session))
    admin.add_view(MerchantAdmin(Merchant, db_session))
