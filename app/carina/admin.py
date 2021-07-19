from flask import Markup
from wtforms.validators import NumberRange

from app.admin.model_views import BaseModelView


class VoucherRetailerAdmin(BaseModelView):
    pass


class VoucherConfigAdmin(BaseModelView):
    can_delete = True
    column_labels = dict(voucherretailer="Voucher retailer")
    column_filters = ("voucherretailer.retailer_slug", "voucher_type_slug")
    column_formatters = dict(
        voucherretailer=lambda v, c, model, p: Markup.escape(model.voucherretailer)
        + Markup("<br />" + f"({model.voucherretailer.id})"),
    )
    form_args = {
        "validity_days": {
            "validators": [
                NumberRange(min=1, message="Must be blank or a positive integer"),
            ],
        }
    }


class VoucherAdmin(BaseModelView):
    column_searchable_list = (
        "voucherconfig.id",
        "voucherconfig.voucher_type_slug",
        "voucherretailer.retailer_slug",
    )
    column_labels = dict(voucherconfig="Voucher config", voucherretailer="Voucher retailer")
    column_filters = ("voucherretailer.retailer_slug", "voucherconfig.voucher_type_slug", "allocated")
    column_formatters = dict(
        voucherconfig=lambda v, c, model, p: Markup.escape(model.voucherconfig)
        + Markup("<br />" + f"({model.voucherconfig.id})"),
        voucherretailer=lambda v, c, model, p: Markup.escape(model.voucherretailer)
        + Markup("<br />" + f"({model.voucherretailer.id})"),
    )
