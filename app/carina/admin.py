from typing import TYPE_CHECKING

from flask import Markup
from retry_tasks_lib.admin.views import (
    RetryTaskAdminBase,
    TaskTypeAdminBase,
    TaskTypeKeyAdminBase,
    TaskTypeKeyValueAdminBase,
)
from wtforms.validators import NumberRange

from app import settings
from app.admin.model_views import BaseModelView
from app.carina.validators import validate_voucher_source

if TYPE_CHECKING:
    from app.carina.db.models import Voucher


def voucher_config_format(view: BaseModelView, context: dict, model: "Voucher", name: str) -> str:
    return Markup(
        (
            "<a href='/bpl/admin/voucher-config/details/?id='{0}' style='white-space: nowrap;'>"
            "<strong>id:</strong> {0}</br>"
            "<strong>type:</strong> {1}</br>"
            "<strong>retailer:</strong> {2}"
            "</a>"
        ).format(model.voucherconfig.id, model.voucherconfig.voucher_type_slug, model.voucherconfig.retailer_slug)
    )


class VoucherConfigAdmin(BaseModelView):
    can_delete = False
    column_filters = ("retailer_slug", "voucher_type_slug")
    form_args = {
        "validity_days": {
            "validators": [
                NumberRange(min=1, message="Must be blank or a positive integer"),
            ],
        }
    }

    form_excluded_columns = ("voucher_collection", "voucherallocation_collection", "created_at", "updated_at")
    form_args = {"fetch_type": {"validators": [validate_voucher_source]}}


class VoucherAdmin(BaseModelView):
    can_create = False
    can_edit = False
    can_delete = False
    column_searchable_list = ("voucherconfig.id", "voucherconfig.voucher_type_slug", "retailer_slug")
    column_labels = {"voucherconfig": "Voucher config"}
    column_filters = ("retailer_slug", "voucherconfig.voucher_type_slug", "allocated")
    column_formatters = {"voucherconfig": voucher_config_format}


class VoucherUpdateAdmin(BaseModelView):
    column_searchable_list = ("id", "voucher_id", "voucher.voucher_code")
    column_filters = ("voucher.retailer_slug",)


class RetryTaskAdmin(BaseModelView, RetryTaskAdminBase):
    endpoint_prefix = settings.CARINA_ENDPOINT_PREFIX
    redis = settings.redis


class TaskTypeAdmin(BaseModelView, TaskTypeAdminBase):
    pass


class TaskTypeKeyAdmin(BaseModelView, TaskTypeKeyAdminBase):
    pass


class TaskTypeKeyValueAdmin(BaseModelView, TaskTypeKeyValueAdminBase):
    pass
