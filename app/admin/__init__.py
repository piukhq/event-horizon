from flask_admin import Admin
from flask_admin.model.form import InlineFormAdmin

from app.db import scoped_session, User, UserProfile
from .classes import MyAdminIndexView, AuthorisedModelView

admin = Admin(name="test flask admin", template_mode="bootstrap3", index_view=MyAdminIndexView())


class UserProfileForm(InlineFormAdmin):
    form_label = "Profile"


class UserAdmin(AuthorisedModelView):
    inline_models = (UserProfileForm(UserProfile),)


with scoped_session() as db_session:
    admin.add_view(UserAdmin(User, db_session))
