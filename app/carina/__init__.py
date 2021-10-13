from typing import TYPE_CHECKING

from retry_tasks_lib.admin.models import RetryTask, TaskType, TaskTypeKey, TaskTypeKeyValue

from app.admin.model_views import BaseModelView

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
            VoucherConfig, db_session, "Voucher Configurations", endpoint="voucher-configs", category=carina_menu_title
        )
    )
    event_horizon_admin.add_view(
        VoucherAdmin(Voucher, db_session, "Vouchers", endpoint="vouchers", category=carina_menu_title)
    )
    event_horizon_admin.add_view(
        VoucherUpdateAdmin(
            VoucherUpdate,
            db_session,
            "Voucher Updates",
            endpoint="voucher-updates",
            category=carina_menu_title,
        )
    )

    event_horizon_admin.add_view(
        RetryTaskAdmin(RetryTask, db_session, "RetryTasks", endpoint="retry_tasks", category=carina_menu_title)
    )
    event_horizon_admin.add_view(
        TaskTypeAdmin(TaskType, db_session, "TaskTypes", endpoint="task_types", category=carina_menu_title)
    )
    event_horizon_admin.add_view(
        TaskTypeKeyAdmin(TaskTypeKey, db_session, "TaskTypeKeys", endpoint="task_type_keys", category=carina_menu_title)
    )
    event_horizon_admin.add_view(
        TaskTypeKeyValueAdmin(
            TaskTypeKeyValue,
            db_session,
            "TaskTypeKeyValues",
            endpoint="task_type_key_values",
            category=carina_menu_title,
        )
    )
