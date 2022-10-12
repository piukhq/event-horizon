from event_horizon.admin.custom_filters import StringInList, StringNotInList
from event_horizon.admin.custom_formatters import format_json_field
from event_horizon.admin.model_views import BaseModelView
from event_horizon.hubble.db import Activity


class ActivityAdmin(BaseModelView):
    can_create = False
    can_edit = False
    can_delete = False
    column_list = (
        "type",
        "summary",
        "user_id",
        "retailer",
        "reasons",
        "activity_identifier",
        "associated_value",
        "datetime",
        "underlying_datetime",
        "campaigns",
        "created_at",
    )
    column_details_list = (
        "type",
        "summary",
        "user_id",
        "retailer",
        "reasons",
        "activity_identifier",
        "associated_value",
        "datetime",
        "underlying_datetime",
        "campaigns",
        "data",
        "created_at",
    )
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