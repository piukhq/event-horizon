from typing import TYPE_CHECKING

from app.vela.admin import (
    CampaignAdmin,
    EarnRuleAdmin,
    ProcessedTransactionAdmin,
    RetailerRewardsAdmin,
    TransactionAdmin,
)

from .db import Campaign, EarnRule, ProcessedTransaction, RetailerRewards, Transaction, db_session

if TYPE_CHECKING:
    from flask_admin import Admin


def register_vela_admin(event_horizon_admin: "Admin") -> None:
    vela_menu_title = "Rewards Management"
    event_horizon_admin.add_view(
        CampaignAdmin(Campaign, db_session, "Campaigns", endpoint="campaigns", category=vela_menu_title)
    )
    event_horizon_admin.add_view(
        EarnRuleAdmin(EarnRule, db_session, "Earn Rules", endpoint="earn-rules", category=vela_menu_title)
    )
    event_horizon_admin.add_view(
        RetailerRewardsAdmin(
            RetailerRewards, db_session, "Retailer Rewards", endpoint="retailer-rewards", category=vela_menu_title
        )
    )
    event_horizon_admin.add_view(
        TransactionAdmin(Transaction, db_session, "Transactions", endpoint="transactions", category=vela_menu_title)
    )
    event_horizon_admin.add_view(
        ProcessedTransactionAdmin(
            ProcessedTransaction,
            db_session,
            "Processed Transactions",
            endpoint="processed-transactions",
            category=vela_menu_title,
        )
    )
