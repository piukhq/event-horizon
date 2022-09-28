from typing import TYPE_CHECKING

from event_horizon.settings import HUBBLE_ENDPOINT_PREFIX

from .admin import ActivityAdmin
from .db import Activity, db_session

if TYPE_CHECKING:
    from flask_admin import Admin


def register_hubble_admin(event_horizon_admin: "Admin") -> None:
    hubble_menu_title = "Activity"
    event_horizon_admin.add_view(
        ActivityAdmin(
            Activity,
            db_session,
            "Activity",
            endpoint=f"{HUBBLE_ENDPOINT_PREFIX}/activity",
            category=hubble_menu_title,
        )
    )
