from typing import TYPE_CHECKING

from event_horizon.settings import CARINA_ENDPOINT_PREFIX

from .admin import (
    FetchTypeAdmin,
    ReadOnlyRewardAdmin,
    RetailerFetchTypeAdmin,
    RewardAdmin,
    RewardCampaignAdmin,
    RewardConfigAdmin,
    RewardFileLogAdmin,
    RewardUpdateAdmin,
)
from .db import (
    FetchType,
    RetailerFetchType,
    Reward,
    RewardCampaign,
    RewardConfig,
    RewardFileLog,
    RewardUpdate,
    db_session,
)

if TYPE_CHECKING:
    from flask_admin import Admin


CARINA_MENU_TITLE = "Rewards Management"


def register_carina_admin(event_horizon_admin: "Admin") -> None:
    event_horizon_admin.add_view(
        FetchTypeAdmin(
            FetchType,
            db_session,
            "Fetch Types",
            endpoint="fetch-types",
            url=f"{CARINA_ENDPOINT_PREFIX}/fetch-types",
            category=CARINA_MENU_TITLE,
        )
    )
    event_horizon_admin.add_view(
        RetailerFetchTypeAdmin(
            RetailerFetchType,
            db_session,
            "Retailer's Fetch Types",
            endpoint="retailer-fetch-types",
            url=f"{CARINA_ENDPOINT_PREFIX}/retailer-fetch-types",
            category=CARINA_MENU_TITLE,
        )
    )
    event_horizon_admin.add_view(
        RewardConfigAdmin(
            RewardConfig,
            db_session,
            "Reward Configurations",
            endpoint="reward-configs",
            url=f"{CARINA_ENDPOINT_PREFIX}/reward-configs",
            category=CARINA_MENU_TITLE,
        )
    )
    event_horizon_admin.add_view(
        RewardAdmin(
            Reward,
            db_session,
            "Rewards",
            endpoint="rewards",
            url=f"{CARINA_ENDPOINT_PREFIX}/rewards",
            category=CARINA_MENU_TITLE,
        )
    )
    event_horizon_admin.add_view(
        ReadOnlyRewardAdmin(
            Reward,
            db_session,
            "Rewards",
            endpoint="ro-rewards",
            url=f"{CARINA_ENDPOINT_PREFIX}/ro-rewards",
            category=CARINA_MENU_TITLE,
        )
    )
    event_horizon_admin.add_view(
        RewardUpdateAdmin(
            RewardUpdate,
            db_session,
            "Reward Updates",
            endpoint="reward-updates",
            url=f"{CARINA_ENDPOINT_PREFIX}/reward-updates",
            category=CARINA_MENU_TITLE,
        )
    )
    event_horizon_admin.add_view(
        RewardCampaignAdmin(
            RewardCampaign,
            db_session,
            "Reward Campaign",
            endpoint="reward-campaign",
            url=f"{CARINA_ENDPOINT_PREFIX}/reward-campaign",
            category=CARINA_MENU_TITLE,
        )
    )
    event_horizon_admin.add_view(
        RewardFileLogAdmin(
            RewardFileLog,
            db_session,
            "Reward File Log",
            endpoint="reward-file-log",
            url=f"{CARINA_ENDPOINT_PREFIX}/reward-file-log",
            category=CARINA_MENU_TITLE,
        )
    )
