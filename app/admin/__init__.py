from flask_admin import Admin

from app.db import get_db_session
from app.db.models import User, MembershipCard, Voucher
from .classes import MyAdminIndexView, AuthorisedModelView

db_session = get_db_session()
admin = Admin(name="test flask admin", template_mode="bootstrap3", index_view=MyAdminIndexView())

# add admin views here
admin.add_view(AuthorisedModelView(User, db_session))
admin.add_view(AuthorisedModelView(MembershipCard, db_session))
admin.add_view(AuthorisedModelView(Voucher, db_session))
