from flask_admin import Admin
from flask_admin.model.form import InlineFormAdmin

from app.db import scoped_session, User, UserProfile, Merchant
from .classes import MyAdminIndexView, AuthorisedModelView

admin = Admin(name="test flask admin", template_mode="bootstrap3", index_view=MyAdminIndexView())


class UserProfileForm(InlineFormAdmin):
    form_label = "Profile"


class UserAdmin(AuthorisedModelView):
    inline_models = (UserProfileForm(UserProfile),)
    form_widget_args = {"created_at": {"disabled": True}}


class MerchantAdmin(AuthorisedModelView):
    form_create_rules = ("name", "slug", "card_number_prefix", "card_number_length")
    form_edit_rules = ("name", "slug", "card_number_prefix", "card_number_length", "created_at")
    form_widget_args = {"created_at": {"disabled": True}}


with scoped_session() as db_session:
    admin.add_view(UserAdmin(User, db_session))
    admin.add_view(MerchantAdmin(Merchant, db_session))
