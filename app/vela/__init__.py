from typing import TYPE_CHECKING

from .admin import CampaignAdmin
from .db import Campaign, db_session

if TYPE_CHECKING:
    from flask_admin import Admin


def register_vela_admin(event_horizon_admin: "Admin") -> None:
    event_horizon_admin.add_view(CampaignAdmin(Campaign, db_session, "Campaigns", endpoint="campaigns"))
