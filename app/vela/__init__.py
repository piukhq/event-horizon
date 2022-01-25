from typing import TYPE_CHECKING

from retry_tasks_lib.db.models import RetryTask, TaskType, TaskTypeKey, TaskTypeKeyValue

from app.settings import VELA_ENDPOINT_PREFIX

from .admin import (
    CampaignAdmin,
    EarnRuleAdmin,
    ProcessedTransactionAdmin,
    RetailerRewardsAdmin,
    RetryTaskAdmin,
    RewardRuleAdmin,
    TaskTypeAdmin,
    TaskTypeKeyAdmin,
    TaskTypeKeyValueAdmin,
    TransactionAdmin,
)
from .db import Campaign, EarnRule, ProcessedTransaction, RetailerRewards, RewardRule, Transaction, db_session

if TYPE_CHECKING:
    from flask_admin import Admin


def register_vela_admin(event_horizon_admin: "Admin") -> None:
    vela_menu_title = "Campaign Management"
    event_horizon_admin.add_view(
        CampaignAdmin(
            Campaign, db_session, "Campaigns", endpoint=f"{VELA_ENDPOINT_PREFIX}/campaigns", category=vela_menu_title
        )
    )
    event_horizon_admin.add_view(
        EarnRuleAdmin(
            EarnRule, db_session, "Earn Rules", endpoint=f"{VELA_ENDPOINT_PREFIX}/earn-rules", category=vela_menu_title
        )
    )
    event_horizon_admin.add_view(
        RewardRuleAdmin(
            RewardRule,
            db_session,
            "Reward Rules",
            endpoint=f"{VELA_ENDPOINT_PREFIX}/reward-rules",
            category=vela_menu_title,
        )
    )
    event_horizon_admin.add_view(
        RetailerRewardsAdmin(
            RetailerRewards,
            db_session,
            "Retailer Rewards",
            endpoint=f"{VELA_ENDPOINT_PREFIX}/retailer-rewards",
            category=vela_menu_title,
        )
    )
    event_horizon_admin.add_view(
        TransactionAdmin(
            Transaction,
            db_session,
            "Transactions",
            endpoint=f"{VELA_ENDPOINT_PREFIX}/transactions",
            category=vela_menu_title,
        )
    )
    event_horizon_admin.add_view(
        ProcessedTransactionAdmin(
            ProcessedTransaction,
            db_session,
            "Processed Transactions",
            endpoint=f"{VELA_ENDPOINT_PREFIX}/processed-transactions",
            category=vela_menu_title,
        )
    )
    event_horizon_admin.add_view(
        RetryTaskAdmin(
            RetryTask,
            db_session,
            "Tasks",
            endpoint=f"{VELA_ENDPOINT_PREFIX}/tasks",
            category=vela_menu_title,
        )
    )
    event_horizon_admin.add_view(
        TaskTypeAdmin(
            TaskType,
            db_session,
            "Task Types",
            endpoint=f"{VELA_ENDPOINT_PREFIX}/task-types",
            category=vela_menu_title,
        )
    )
    event_horizon_admin.add_view(
        TaskTypeKeyAdmin(
            TaskTypeKey,
            db_session,
            "Task Type Keys",
            endpoint=f"{VELA_ENDPOINT_PREFIX}/task-type-keys",
            category=vela_menu_title,
        )
    )
    event_horizon_admin.add_view(
        TaskTypeKeyValueAdmin(
            TaskTypeKeyValue,
            db_session,
            "Task Type Key Values",
            endpoint=f"{VELA_ENDPOINT_PREFIX}/task-type-key-values",
            category=vela_menu_title,
        )
    )
