from typing import TYPE_CHECKING

from event_horizon.settings import POLARIS_ENDPOINT_PREFIX

from .admin import (
    AccountHolderAdmin,
    AccountHolderCampaignBalanceAdmin,
    AccountHolderMarketingPreferenceAdmin,
    AccountHolderPendingRewardAdmin,
    AccountHolderProfileAdmin,
    AccountHolderRewardAdmin,
    AccountHolderTransactionHistoryAdmin,
    EmailTemplateAdmin,
    EmailTemplateKeyAdmin,
    ReadOnlyAccountHolderRewardAdmin,
    RetailerConfigAdmin,
)
from .db import (
    AccountHolder,
    AccountHolderCampaignBalance,
    AccountHolderMarketingPreference,
    AccountHolderPendingReward,
    AccountHolderProfile,
    AccountHolderReward,
    AccountHolderTransactionHistory,
    EmailTemplate,
    EmailTemplateKey,
    RetailerConfig,
    db_session,
)

if TYPE_CHECKING:
    from flask_admin import Admin

POLARIS_MENU_TITLE = "Customer Management"


def register_polaris_admin(event_horizon_admin: "Admin") -> None:
    event_horizon_admin.add_view(
        AccountHolderAdmin(
            AccountHolder,
            db_session,
            "Account Holders",
            endpoint="account-holders",
            url=f"{POLARIS_ENDPOINT_PREFIX}/account-holders",
            category=POLARIS_MENU_TITLE,
        )
    )
    event_horizon_admin.add_view(
        AccountHolderProfileAdmin(
            AccountHolderProfile,
            db_session,
            "Profiles",
            endpoint="profiles",
            url=f"{POLARIS_ENDPOINT_PREFIX}/profiles",
            category=POLARIS_MENU_TITLE,
        )
    )
    event_horizon_admin.add_view(
        AccountHolderMarketingPreferenceAdmin(
            AccountHolderMarketingPreference,
            db_session,
            "Marketing Preferences",
            endpoint="marketing-preferences",
            url=f"{POLARIS_ENDPOINT_PREFIX}/marketing-preferences",
            category=POLARIS_MENU_TITLE,
        )
    )
    event_horizon_admin.add_view(
        AccountHolderRewardAdmin(
            AccountHolderReward,
            db_session,
            "Account Holder Rewards",
            endpoint="account-holder-rewards",
            url=f"{POLARIS_ENDPOINT_PREFIX}/account-holder-rewards",
            category=POLARIS_MENU_TITLE,
        )
    )
    event_horizon_admin.add_view(
        ReadOnlyAccountHolderRewardAdmin(
            AccountHolderReward,
            db_session,
            "Account Holder Rewards",
            endpoint="ro-account-holder-rewards",
            url=f"{POLARIS_ENDPOINT_PREFIX}/ro-account-holder-rewards",
            category=POLARIS_MENU_TITLE,
        )
    )
    event_horizon_admin.add_view(
        AccountHolderPendingRewardAdmin(
            AccountHolderPendingReward,
            db_session,
            "Account Holder Pending Rewards",
            endpoint="account-holder-pending-rewards",
            url=f"{POLARIS_ENDPOINT_PREFIX}/account-holder-pending-rewards",
            category=POLARIS_MENU_TITLE,
        )
    )
    event_horizon_admin.add_view(
        AccountHolderCampaignBalanceAdmin(
            AccountHolderCampaignBalance,
            db_session,
            "Account Holder Campaign Balances",
            endpoint="account-holder-campaign-balances",
            url=f"{POLARIS_ENDPOINT_PREFIX}/account-holder-campaign-balances",
            category=POLARIS_MENU_TITLE,
        )
    )
    event_horizon_admin.add_view(
        AccountHolderTransactionHistoryAdmin(
            AccountHolderTransactionHistory,
            db_session,
            "Account Holder Transaction History",
            endpoint="account-holder-transaction-history",
            url=f"{POLARIS_ENDPOINT_PREFIX}/account-holder-transaction-history",
            category=POLARIS_MENU_TITLE,
        )
    )
    event_horizon_admin.add_view(
        RetailerConfigAdmin(
            RetailerConfig,
            db_session,
            "Retailers' Config",
            endpoint="retailers-config",
            url=f"{POLARIS_ENDPOINT_PREFIX}/retailers-config",
            category=POLARIS_MENU_TITLE,
        )
    )
    event_horizon_admin.add_view(
        EmailTemplateAdmin(
            EmailTemplate,
            db_session,
            "Email Templates",
            endpoint="email-templates",
            url=f"{POLARIS_ENDPOINT_PREFIX}/email-templates",
            category=POLARIS_MENU_TITLE,
        )
    )
    event_horizon_admin.add_view(
        EmailTemplateKeyAdmin(
            EmailTemplateKey,
            db_session,
            "Email Template Keys",
            endpoint="email-template-keys",
            url=f"{POLARIS_ENDPOINT_PREFIX}/email-template-keys",
            category=POLARIS_MENU_TITLE,
        )
    )
