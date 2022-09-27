from flask_admin import Admin

from event_horizon.settings import ROUTE_BASE

from .views import EventHorizonAdminIndexView

event_horizon_admin = Admin(
    name="Event Horizon",
    template_mode="bootstrap3",  # Note: checkbox validation errors (invalid-feedback) are not displayed with bootstrap4
    index_view=EventHorizonAdminIndexView(url=f"{ROUTE_BASE}/"),
    base_template="eh_master.html",
)
