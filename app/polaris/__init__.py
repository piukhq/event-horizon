from typing import TYPE_CHECKING

from retry_tasks_lib.db.models import RetryTask, TaskType, TaskTypeKey, TaskTypeKeyValue

from app.settings import POLARIS_ENDPOINT_PREFIX

from .admin import (
    AccountHolderAdmin,
    AccountHolderCampaignBalanceAdmin,
    AccountHolderProfileAdmin,
    AccountHolderVoucherAdmin,
    RetailerConfigAdmin,
    RetryTaskAdmin,
    TaskTypeAdmin,
    TaskTypeKeyAdmin,
    TaskTypeKeyValueAdmin,
)
from .db import (
    AccountHolder,
    AccountHolderCampaignBalance,
    AccountHolderProfile,
    AccountHolderVoucher,
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
        AccountHolderVoucherAdmin(
            AccountHolderVoucher,
            db_session,
            "Account Holder Vouchers",
            endpoint=f"{POLARIS_ENDPOINT_PREFIX}/account-holder-vouchers",
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
        AccountHolderCampaignBalanceAdmin(
            AccountHolderCampaignBalance,
            db_session,
            "Account Holder Campaign Balances",
            endpoint=f"{POLARIS_ENDPOINT_PREFIX}/account-holder-campaign-balances",
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
