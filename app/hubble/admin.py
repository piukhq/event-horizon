from app.admin.custom_filters import StringInList, StringNotInList
from app.admin.custom_formatters import format_json_field
from app.admin.model_views import BaseModelView
from app.hubble.db.models import Activity


class ActivityAdmin(BaseModelView):
    can_create = False
    can_edit = False
    can_delete = False
    column_searchable_list = ("user_id",)
    column_filters = (
        "underlying_datetime",
        "type",
        "retailer",
        "activity_identifier",
        StringInList(Activity.reasons, "Reasons"),
        StringNotInList(Activity.reasons, "Reasons"),
        StringInList(Activity.campaigns, "Campaigns"),
        StringNotInList(Activity.campaigns, "Campaigns"),
    )
    column_formatters = {"data": format_json_field}
