from typing import TYPE_CHECKING

from retry_tasks_lib.db.models import RetryTask, TaskType, TaskTypeKey, TaskTypeKeyValue

from app.settings import POLARIS_ENDPOINT_PREFIX

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
    RetailerConfigAdmin,
    RetryTaskAdmin,
    TaskTypeAdmin,
    TaskTypeKeyAdmin,
    TaskTypeKeyValueAdmin,
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


def register_polaris_admin(event_horizon_admin: "Admin") -> None:
    polaris_menu_title = "Customer Management"
    event_horizon_admin.add_view(
        AccountHolderAdmin(
            AccountHolder,
            db_session,
            "Account Holders",
            endpoint=f"{POLARIS_ENDPOINT_PREFIX}/account-holders",
            category=polaris_menu_title,
        )
    )
    event_horizon_admin.add_view(
        AccountHolderProfileAdmin(
            AccountHolderProfile,
            db_session,
            "Profiles",
            endpoint=f"{POLARIS_ENDPOINT_PREFIX}/profiles",
            category=polaris_menu_title,
        )
    )
    event_horizon_admin.add_view(
        AccountHolderMarketingPreferenceAdmin(
            AccountHolderMarketingPreference,
            db_session,
            "Marketing Preferences",
            endpoint=f"{POLARIS_ENDPOINT_PREFIX}/marketing-preferences",
            category=polaris_menu_title,
        )
    )
    event_horizon_admin.add_view(
        AccountHolderRewardAdmin(
            AccountHolderReward,
            db_session,
            "Account Holder Rewards",
            endpoint=f"{POLARIS_ENDPOINT_PREFIX}/account-holder-rewards",
            category=polaris_menu_title,
        )
    )
    event_horizon_admin.add_view(
        AccountHolderPendingRewardAdmin(
            AccountHolderPendingReward,
            db_session,
            "Account Holder Pending Rewards",
            endpoint=f"{POLARIS_ENDPOINT_PREFIX}/account-holder-pending-rewards",
            category=polaris_menu_title,
        )
    )
    event_horizon_admin.add_view(
        AccountHolderCampaignBalanceAdmin(
            AccountHolderCampaignBalance,
            db_session,
            "Account Holder Campaign Balances",
            endpoint=f"{POLARIS_ENDPOINT_PREFIX}/account-holder-campaign-balances",
            category=polaris_menu_title,
        )
    )
    event_horizon_admin.add_view(
        AccountHolderTransactionHistoryAdmin(
            AccountHolderTransactionHistory,
            db_session,
            "Account Holder Trasnaction History",
            endpoint=f"{POLARIS_ENDPOINT_PREFIX}/account-holder-transaction-history",
            category=polaris_menu_title,
        )
    )
    event_horizon_admin.add_view(
        RetailerConfigAdmin(
            RetailerConfig,
            db_session,
            "Retailers' Config",
            endpoint=f"{POLARIS_ENDPOINT_PREFIX}/retailers-config",
            category=polaris_menu_title,
        )
    )
    event_horizon_admin.add_view(
        EmailTemplateAdmin(
            EmailTemplate,
            db_session,
            "Email Templates",
            endpoint=f"{POLARIS_ENDPOINT_PREFIX}/email-templates",
            category=polaris_menu_title,
        )
    )
    event_horizon_admin.add_view(
        EmailTemplateKeyAdmin(
            EmailTemplateKey,
            db_session,
            "Email Template Keys",
            endpoint=f"{POLARIS_ENDPOINT_PREFIX}/email-template-keys",
            category=polaris_menu_title,
        )
    )
    event_horizon_admin.add_view(
        RetryTaskAdmin(
            RetryTask,
            db_session,
            "Tasks",
            endpoint=f"{POLARIS_ENDPOINT_PREFIX}/tasks",
            category=polaris_menu_title,
        )
    )
    event_horizon_admin.add_view(
        TaskTypeAdmin(
            TaskType,
            db_session,
            "Task Types",
            endpoint=f"{POLARIS_ENDPOINT_PREFIX}/task-types",
            category=polaris_menu_title,
        )
    )
    event_horizon_admin.add_view(
        TaskTypeKeyAdmin(
            TaskTypeKey,
            db_session,
            "Task Type Keys",
            endpoint=f"{POLARIS_ENDPOINT_PREFIX}/task-type-keys",
            category=polaris_menu_title,
        )
    )
    event_horizon_admin.add_view(
        TaskTypeKeyValueAdmin(
            TaskTypeKeyValue,
            db_session,
            "Task Type Key Values",
            endpoint=f"{POLARIS_ENDPOINT_PREFIX}/task-type-key-values",
            category=polaris_menu_title,
        )
    )
