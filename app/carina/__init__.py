from typing import TYPE_CHECKING

from retry_tasks_lib.db.models import RetryTask, TaskType, TaskTypeKey, TaskTypeKeyValue

from app.settings import CARINA_ENDPOINT_PREFIX

from .admin import (
    RetryTaskAdmin,
    RewardAdmin,
    RewardConfigAdmin,
    RewardUpdateAdmin,
    TaskTypeAdmin,
    TaskTypeKeyAdmin,
    TaskTypeKeyValueAdmin,
)
from .db import Reward, RewardConfig, RewardUpdate, db_session

if TYPE_CHECKING:
    from flask_admin import Admin


def register_carina_admin(event_horizon_admin: "Admin") -> None:
    carina_menu_title = "Reward Management"
    event_horizon_admin.add_view(
        RewardConfigAdmin(
            RewardConfig,
            db_session,
            "Reward Configurations",
            endpoint=f"{CARINA_ENDPOINT_PREFIX}/reward-configs",
            category=carina_menu_title,
        )
    )
    event_horizon_admin.add_view(
        RewardAdmin(
            Reward,
            db_session,
            "Rewards",
            endpoint=f"{CARINA_ENDPOINT_PREFIX}/rewards",
            category=carina_menu_title,
        )
    )
    event_horizon_admin.add_view(
        RewardUpdateAdmin(
            RewardUpdate,
            db_session,
            "Reward Updates",
            endpoint=f"{CARINA_ENDPOINT_PREFIX}/reward-updates",
            category=carina_menu_title,
        )
    )
    event_horizon_admin.add_view(
        RetryTaskAdmin(
            RetryTask,
            db_session,
            name="Tasks",
            endpoint=f"{CARINA_ENDPOINT_PREFIX}/tasks",
            category=carina_menu_title,
        )
    )
    event_horizon_admin.add_view(
        TaskTypeAdmin(
            TaskType,
            db_session,
            name="Task Types",
            endpoint=f"{CARINA_ENDPOINT_PREFIX}/task-types",
            category=carina_menu_title,
        )
    )
    event_horizon_admin.add_view(
        TaskTypeKeyAdmin(
            TaskTypeKey,
            db_session,
            name="Task Type Keys",
            endpoint=f"{CARINA_ENDPOINT_PREFIX}/task-type-keys",
            category=carina_menu_title,
        )
    )
    event_horizon_admin.add_view(
        TaskTypeKeyValueAdmin(
            TaskTypeKeyValue,
            db_session,
            "Task Type Key Values",
            endpoint=f"{CARINA_ENDPOINT_PREFIX}/task-type-key-values",
            category=carina_menu_title,
        )
    )
