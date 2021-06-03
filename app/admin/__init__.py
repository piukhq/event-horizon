from flask_admin import Admin

from .views import EventHorizonAdminIndexView

event_horizon_admin = Admin(
    name="Event Horizon",
    template_mode="bootstrap3",  # Note: checkbox validation errors (invalid-feedback) are not displayed with bootstrap4
    index_view=EventHorizonAdminIndexView(url="/bpl/admin/"),
)
