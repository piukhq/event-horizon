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
