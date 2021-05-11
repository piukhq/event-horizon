from flask_admin import Admin

from .views import EventHorizonAdminIndexView

event_horizon_admin = Admin(
    name="Event Horizon", template_mode="bootstrap4", index_view=EventHorizonAdminIndexView(url="/bpl/admin/")
)
