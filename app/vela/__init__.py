from typing import TYPE_CHECKING

from app.vela.admin import CampaignAdmin, EarnRuleAdmin, RetailerRewardsAdmin
from app.vela.db.models import EarnRule, RetailerRewards

from .db import Campaign, EarnRule, db_session

if TYPE_CHECKING:
    from flask_admin import Admin


def register_vela_admin(event_horizon_admin: "Admin") -> None:
    event_horizon_admin.add_view(CampaignAdmin(Campaign, db_session, "Campaigns", endpoint="campaigns"))
    event_horizon_admin.add_view(EarnRuleAdmin(EarnRule, db_session, "Earn Rules", endpoint="earn-rules"))
    event_horizon_admin.add_view(
        RetailerRewardsAdmin(RetailerRewards, db_session, "Retailer Rewards", endpoint="retailer-rewards")
    )
