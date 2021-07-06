from app.admin.model_views import BaseModelView


class VoucherConfigAdmin(BaseModelView):
    can_delete = True
    column_filters = ("retailer_slug", "voucher_type_slug")
