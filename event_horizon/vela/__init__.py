from typing import TYPE_CHECKING

from event_horizon.settings import VELA_ENDPOINT_PREFIX

from .admin import (
    CampaignAdmin,
    EarnRuleAdmin,
    ProcessedTransactionAdmin,
    RetailerRewardsAdmin,
    RetailerStoreAdmin,
    RewardRuleAdmin,
    TransactionAdmin,
)
from .db import (
    Campaign,
    EarnRule,
    ProcessedTransaction,
    RetailerRewards,
    RetailerStore,
    RewardRule,
    Transaction,
    db_session,
)

if TYPE_CHECKING:
    from flask_admin import Admin


VELA_MENU_TITLE = "Retailer Campaign Management"


def register_vela_admin(event_horizon_admin: "Admin") -> None:
    event_horizon_admin.add_view(
        RetailerRewardsAdmin(
            RetailerRewards,
            db_session,
            "Retailer Rewards",
            endpoint="retailer-rewards",
            url=f"{VELA_ENDPOINT_PREFIX}/retailer-rewards",
            category=VELA_MENU_TITLE,
        )
    )
    event_horizon_admin.add_view(
        RetailerStoreAdmin(
            RetailerStore,
            db_session,
            "Retailer's Stores",
            endpoint="retailer-stores",
            url=f"{VELA_ENDPOINT_PREFIX}/retailer-stores",
            category=VELA_MENU_TITLE,
        )
    )
    event_horizon_admin.add_view(
        CampaignAdmin(
            Campaign,
            db_session,
            "Campaigns",
            endpoint="campaigns",
            url=f"{VELA_ENDPOINT_PREFIX}/campaigns",
            category=VELA_MENU_TITLE,
        )
    )
    event_horizon_admin.add_view(
        EarnRuleAdmin(
            EarnRule,
            db_session,
            "Earn Rules",
            endpoint="earn-rules",
            url=f"{VELA_ENDPOINT_PREFIX}/earn-rules",
            category=VELA_MENU_TITLE,
        )
    )
    event_horizon_admin.add_view(
        RewardRuleAdmin(
            RewardRule,
            db_session,
            "Reward Rules",
            endpoint="reward-rules",
            url=f"{VELA_ENDPOINT_PREFIX}/reward-rules",
            category=VELA_MENU_TITLE,
        )
    )
    event_horizon_admin.add_view(
        TransactionAdmin(
            Transaction,
            db_session,
            "Transactions",
            endpoint="transactions",
            url=f"{VELA_ENDPOINT_PREFIX}/transactions",
            category=VELA_MENU_TITLE,
        )
    )
    event_horizon_admin.add_view(
        ProcessedTransactionAdmin(
            ProcessedTransaction,
            db_session,
            "Processed Transactions",
            endpoint="processed-transactions",
            url=f"{VELA_ENDPOINT_PREFIX}/processed-transactions",
            category=VELA_MENU_TITLE,
        )
    )
