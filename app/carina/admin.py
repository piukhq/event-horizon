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
from app.carina.validators import validate_required_fields_values, validate_retailer_fetch_type

if TYPE_CHECKING:
    from app.carina.db.models import Reward


def reward_config_format(view: BaseModelView, context: dict, model: "Reward", name: str) -> str:
    return Markup(
        (
            f"<a href='{settings.ROUTE_BASE}/reward-config/details/?id='{0}' style='white-space: nowrap;'>"
            "<strong>id:</strong> {0}</br>"
            "<strong>type:</strong> {1}</br>"
            "<strong>retailer:</strong> {2}"
            "</a>"
        ).format(model.rewardconfig.id, model.rewardconfig.reward_slug, model.rewardconfig.retailer.slug)
    )


class FetchTypeAdmin(BaseModelView):
    can_create = False
    can_edit = False
    can_delete = False
    column_searchable_list = ("name",)


class RetailerFetchTypeAdmin(BaseModelView):
    can_create = True
    can_edit = True
    can_delete = True
    column_searchable_list = ("retailer.slug", "fetchtype.name")


class RewardConfigAdmin(BaseModelView):
    can_delete = False
    column_filters = ("retailer.slug", "reward_slug")
    form_args = {
        "validity_days": {
            "validators": [
                NumberRange(min=1, message="Must be blank or a positive integer"),
            ],
        }
    }

    form_excluded_columns = ("reward_collection", "rewardallocation_collection", "created_at", "updated_at")
    form_args = {
        "fetchtype": {"validators": [validate_retailer_fetch_type]},
        "required_fields_values": {"validators": [validate_required_fields_values]},
    }


class RewardAdmin(BaseModelView):
    can_create = False
    can_edit = False
    can_delete = False
    column_searchable_list = ("rewardconfig.id", "rewardconfig.reward_slug", "retailer.slug")
    column_labels = {"rewardconfig": "Reward config"}
    column_filters = ("retailer.slug", "rewardconfig.reward_slug", "allocated")
    column_formatters = {"rewardconfig": reward_config_format}


class RewardUpdateAdmin(BaseModelView):
    column_searchable_list = ("id", "reward_uuid", "reward.code")
    column_filters = ("reward.retailer.slug",)


class RetryTaskAdmin(BaseModelView, RetryTaskAdminBase):
    endpoint_prefix = settings.CARINA_ENDPOINT_PREFIX
    redis = settings.redis


class TaskTypeAdmin(BaseModelView, TaskTypeAdminBase):
    pass


class TaskTypeKeyAdmin(BaseModelView, TaskTypeKeyAdminBase):
    pass


class TaskTypeKeyValueAdmin(BaseModelView, TaskTypeKeyValueAdminBase):
    pass
