from typing import TYPE_CHECKING, Union

from flask import Markup
from wtforms.validators import NumberRange

from app.admin.model_views import AuthorisedModelView, BaseModelView

if TYPE_CHECKING:
    from app.carina.db.models import Voucher, VoucherAllocation


def voucher_config_format(
    view: BaseModelView, context: dict, model: Union["Voucher", "VoucherAllocation"], name: str
) -> str:
    return Markup(
        (
            "<a href='/bpl/admin/voucher-config/details/?id='{0}' style='white-space: nowrap;'>"
            "<strong>id:</strong> {0}</br>"
            "<strong>type:</strong> {1}</br>"
            "<strong>retailer:</strong> {2}"
            "</a>"
        ).format(model.voucherconfig.id, model.voucherconfig.voucher_type_slug, model.voucherconfig.retailer_slug)
    )


def voucher_format(view: BaseModelView, context: dict, model: "VoucherAllocation", name: str) -> str:
    return Markup(("<a href='/bpl/admin/vouchers/details/?id={0}'>{0}</a>").format(model.voucher.id))


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


class VoucherAdmin(BaseModelView):
    can_create = False
    can_edit = False
    can_delete = False
    column_searchable_list = ("voucherconfig.id", "voucherconfig.voucher_type_slug", "retailer_slug")
    column_labels = {"voucherconfig": "Voucher config"}
    column_filters = ("retailer_slug", "voucherconfig.voucher_type_slug", "allocated")
    column_formatters = {"voucherconfig": voucher_config_format}


class VoucherAllocationAdmin(AuthorisedModelView):
    column_searchable_list = ("id", "voucher.id")
    column_exclude_list = ("response_data", "account_url")
    column_filters = ("voucherconfig.retailer_slug", "voucherconfig.voucher_type_slug", "voucherconfig.id")
    column_labels = {"voucherconfig": "Voucher config"}
    column_formatters = {"voucherconfig": voucher_config_format, "voucher": voucher_format}
