from typing import TYPE_CHECKING

from retry_tasks_lib.db.models import RetryTask, TaskType, TaskTypeKey, TaskTypeKeyValue

from app.settings import CARINA_ENDPOINT_PREFIX

from .admin import (
    RetryTaskAdmin,
    TaskTypeAdmin,
    TaskTypeKeyAdmin,
    TaskTypeKeyValueAdmin,
    VoucherAdmin,
    VoucherConfigAdmin,
    VoucherUpdateAdmin,
)
from .db import Voucher, VoucherConfig, VoucherUpdate, db_session

if TYPE_CHECKING:
    from flask_admin import Admin


def register_carina_admin(event_horizon_admin: "Admin") -> None:
    carina_menu_title = "Voucher Management"
    event_horizon_admin.add_view(
        VoucherConfigAdmin(
            VoucherConfig,
            db_session,
            "Voucher Configurations",
            endpoint=f"{CARINA_ENDPOINT_PREFIX}/voucher-configs",
            category=carina_menu_title,
        )
    )
    event_horizon_admin.add_view(
        VoucherAdmin(
            Voucher,
            db_session,
            "Vouchers",
            endpoint=f"{CARINA_ENDPOINT_PREFIX}/vouchers",
            category=carina_menu_title,
        )
    )
    event_horizon_admin.add_view(
        VoucherUpdateAdmin(
            VoucherUpdate,
            db_session,
            "Voucher Updates",
            endpoint=f"{CARINA_ENDPOINT_PREFIX}/voucher-updates",
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
