from flask import Markup
from wtforms.validators import NumberRange

from app.admin.model_views import BaseModelView


class VoucherConfigAdmin(BaseModelView):
    can_delete = True
    column_filters = ("retailer_slug", "voucher_type_slug")
    form_args = {
        "validity_days": {
            "validators": [
                NumberRange(min=1, message="Must be blank or a positive integer"),
            ],
        }
    }


class VoucherAdmin(BaseModelView):
    column_searchable_list = ("voucherconfig.id", "voucherconfig.voucher_type_slug", "voucherconfig.retailer_slug")
    column_labels = dict(voucherconfig="Voucher config")
    column_filters = ("voucherconfig.retailer_slug", "voucherconfig.voucher_type_slug", "allocated")
    column_formatters = dict(
        voucherconfig=lambda v, c, model, p: Markup.escape(model.voucherconfig)
        + Markup("<br />" + f"({model.voucherconfig.id})")
    )
