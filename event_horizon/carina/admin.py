import logging

from datetime import datetime, timezone
from typing import TYPE_CHECKING

import requests

from flask import Markup, flash, redirect, url_for
from flask_admin.actions import action
from requests import RequestException
from sqlalchemy.future import select

from event_horizon import settings
from event_horizon.activity_utils.enums import ActivityType
from event_horizon.activity_utils.tasks import sync_send_activity
from event_horizon.admin.model_views import BaseModelView, CanDeleteModelView
from event_horizon.carina.db import Reward, RewardConfig
from event_horizon.carina.db.models import Retailer
from event_horizon.carina.validators import (
    validate_optional_yaml,
    validate_required_fields_values_yaml,
    validate_retailer_fetch_type,
)

if TYPE_CHECKING:
    from jinja2.runtime import Context
    from werkzeug.wrappers import Response


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


def reward_file_log_format(_v: type[BaseModelView], _c: "Context", model: "Reward", _p: str) -> str | None:
    return (
        Markup("<strong><a href='{0}'>{1}</a></strong>").format(
            url_for("reward-file-log.details_view", id=model.rewardfilelog.id), model.rewardfilelog.file_name
        )
        if model.rewardfilelog
        else None
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
        if reward_config := self.session.get(RewardConfig, reward_config_id):
            return reward_config
        raise ValueError(f"No RewardConfig with id {reward_config_id}")


class RewardAdmin(BaseModelView):
    can_create = False
    can_edit = False
    can_delete = False
    column_searchable_list = ("rewardconfig.id", "rewardconfig.reward_slug", "retailer.slug")
    column_labels = {"rewardconfig": "Reward config", "rewardfilelog": "Reward filename"}
    column_filters = ("retailer.slug", "rewardconfig.reward_slug", "allocated", "deleted", "rewardfilelog.file_name")
    column_formatters = {"rewardconfig": reward_config_format, "rewardfilelog": reward_file_log_format}

    def is_accessible(self) -> bool:
        return super().is_accessible() if self.is_read_write_user else False

    def inaccessible_callback(self, name: str, **kwargs: dict | None) -> "Response":
        if self.is_read_write_user:
            return redirect(url_for("rewards.index_view"))

        if self.is_read_only_user:
            return redirect(url_for("ro-rewards.index_view"))

        return super().inaccessible_callback(name, **kwargs)

    def is_action_allowed(self, name: str) -> bool:
        if name == "delete-rewards":
            return self.is_read_write_user

        return super().is_action_allowed(name)

    def _get_rewards_from_ids(self, reward_ids: list[str]) -> list[Reward]:
        return self.session.execute(select(Reward).where(Reward.id.in_(reward_ids))).scalars().all()

    def _get_retailer_by_id(self, retailer_id: int) -> Retailer:
        return self.session.execute(select(Retailer).where(Retailer.id == retailer_id)).scalar_one()

    @action(
        "delete-rewards",
        "Delete",
        "This action can only be carried out on non allocated and non soft deleted rewards."
        "This action is unreversible. Proceed?",
    )
    def delete_rewards(self, reward_ids: list[str]) -> None:
        # Get rewards for all selected ids
        rewards = self._get_rewards_from_ids(reward_ids)

        selected_retailer_id: int = rewards[0].retailer_id
        for reward in rewards:
            # Fail if all rewards are not eligible for deleting
            if reward.retailer_id != selected_retailer_id:
                self.session.rollback()
                flash("Not all selected rewards are for the same retailer", category="error")
                return

            if reward.allocated or reward.deleted:
                self.session.rollback()
                flash("Not all selected rewards are eligible for deletion", category="error")
                return

            self.session.delete(reward)

        self.session.commit()

        # Synchronously send activity for rewards deleted if successfully deleted
        rewards_deleted_count = len(rewards)
        retailer = self._get_retailer_by_id(selected_retailer_id)
        activity_payload = ActivityType.get_reward_deleted_activity_data(
            activity_datetime=datetime.now(tz=timezone.utc),
            retailer_slug=retailer.slug,
            sso_username=self.sso_username,
            rewards_deleted_count=rewards_deleted_count,
        )
        sync_send_activity(activity_payload, routing_key=ActivityType.REWARD_DELETED.value)
        flash("Successfully deleted selected rewards")


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


class RewardCampaignAdmin(BaseModelView):
    can_create = False
    can_edit = False
    can_delete = False
    column_searchable_list = ("id",)
    column_filters = ("retailer.slug", "reward_slug", "campaign_slug", "campaign_status")


class RewardFileLogAdmin(BaseModelView):
    can_create = False
    can_edit = False
    can_delete = False
    column_searchable_list = ("id", "file_name")
    column_filters = ("file_name", "file_agent_type", "created_at")
