import logging

from typing import TYPE_CHECKING

import requests

from flask import Markup, flash, redirect, url_for
from flask_admin.actions import action
from requests import RequestException
from retry_tasks_lib.admin.views import (
    RetryTaskAdminBase,
    TaskTypeAdminBase,
    TaskTypeKeyAdminBase,
    TaskTypeKeyValueAdminBase,
)

from event_horizon import settings
from event_horizon.admin.model_views import BaseModelView, CanDeleteModelView
from event_horizon.carina.db import RewardConfig
from event_horizon.carina.validators import (
    validate_optional_yaml,
    validate_required_fields_values_yaml,
    validate_retailer_fetch_type,
)

if TYPE_CHECKING:
    from werkzeug.wrappers import Response

    from event_horizon.carina.db import Reward

# pylint: disable=unused-argument
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
    column_formatters = {
        "required_fields": lambda v, c, model, p: Markup("<pre>")
        + Markup.escape(model.required_fields)
        + Markup("</pre>"),
    }


class RetailerFetchTypeAdmin(CanDeleteModelView):
    column_searchable_list = ("retailer.slug", "fetchtype.name")
    form_widget_args = {
        "agent_config": {"rows": 5},
    }
    column_formatters = {
        "agent_config": lambda v, c, model, p: Markup("<pre>") + Markup.escape(model.agent_config) + Markup("</pre>"),
    }
    form_args = {
        "agent_config": {
            "description": "Optional configuration in YAML format",
            "validators": [
                validate_optional_yaml,
            ],
        },
    }


class RewardConfigAdmin(BaseModelView):
    column_filters = ("retailer.slug", "reward_slug")
    form_excluded_columns = ("reward_collection", "rewardallocation_collection", "created_at", "updated_at")
    form_widget_args = {
        "required_fields_values": {"rows": 5},
    }
    form_args = {
        "fetchtype": {
            "validators": [
                validate_retailer_fetch_type,
            ]
        },
        "required_fields_values": {
            "description": "Optional configuration in YAML format",
            "validators": [
                validate_required_fields_values_yaml,
            ],
        },
    }
    column_formatters = {
        "required_fields_values": lambda v, c, model, p: Markup("<pre>")
        + Markup.escape(model.required_fields_values)
        + Markup("</pre>"),
    }

    @action(
        "deactivate-reward-type",
        "DEACTIVATE",
        "This action can only be carried out on one reward_config at a time and is not reversible."
        " Are you sure you wish to proceed?",
    )
    def deactivate_reward_type(self, reward_config_ids: list[str]) -> None:
        if len(reward_config_ids) != 1:
            flash("This action must be completed for reward_configs one at a time", category="error")
            return
        try:
            reward_config = self._get_reward_config(int(reward_config_ids[0]))
            resp = requests.delete(
                f"{settings.CARINA_BASE_URL}/{reward_config.retailer.slug}/rewards/{reward_config.reward_slug}",
                headers={"Authorization": f"token {settings.CARINA_AUTH_TOKEN}"},
                timeout=settings.REQUEST_TIMEOUT,
            )
            if 200 <= resp.status_code <= 204:
                flash("Successfully diactivated reward_config")
            else:
                self._flash_error_response(resp.json())

        except (ValueError, RequestException) as exc:
            flash(exc.args[0], category="error")
            logging.exception("Could not deactivate reward type", exc_info=exc)

    def _get_reward_config(self, reward_config_id: int) -> RewardConfig:
        reward_config: RewardConfig | None = self.session.get(RewardConfig, reward_config_id)
        if not reward_config:
            raise ValueError(f"No RewardConfig with id {reward_config_id}")
        return reward_config


class RewardAdmin(BaseModelView):
    can_create = False
    can_edit = False
    can_delete = False
    column_searchable_list = ("rewardconfig.id", "rewardconfig.reward_slug", "retailer.slug")
    column_labels = {"rewardconfig": "Reward config"}
    column_filters = ("retailer.slug", "rewardconfig.reward_slug", "allocated")
    column_formatters = {"rewardconfig": reward_config_format}

    def is_accessible(self) -> bool:
        if not self.is_read_write_user:
            return False

        return super().is_accessible()

    def inaccessible_callback(self, name: str, **kwargs: dict | None) -> "Response":
        if self.user_roles.intersection(self.RW_AZURE_ROLES):
            return redirect(url_for(f"{settings.CARINA_ENDPOINT_PREFIX}/rewards.index_view"))

        if self.user_roles.intersection(self.RO_AZURE_ROLES):
            return redirect(url_for(f"{settings.CARINA_ENDPOINT_PREFIX}/ro-rewards.index_view"))

        return super().inaccessible_callback(name, **kwargs)


class ReadOnlyRewardAdmin(RewardAdmin):
    column_details_exclude_list = ["code"]
    column_export_exclude_list = ["code"]
    column_exclude_list = ["code"]

    def is_accessible(self) -> bool:
        if self.is_read_write_user:
            return False

        return super(RewardAdmin, self).is_accessible()


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
