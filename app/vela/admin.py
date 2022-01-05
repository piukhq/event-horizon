import logging

from typing import TYPE_CHECKING, Optional, Tuple, Union

import requests
import wtforms

from flask import flash
from flask_admin.actions import action
from flask_admin.model import typefmt
from retry_tasks_lib.admin.views import (
    RetryTaskAdminBase,
    TaskTypeAdminBase,
    TaskTypeKeyAdminBase,
    TaskTypeKeyValueAdminBase,
)
from sqlalchemy.future import select
from wtforms.validators import DataRequired

from app import settings
from app.admin.model_views import BaseModelView, CanDeleteModelView
from app.vela.db.models import Campaign, RetailerRewards
from app.vela.validators import (
    validate_campaign_earn_inc_is_tx_value,
    validate_campaign_status_change,
    validate_earn_rule_deletion,
    validate_earn_rule_increment,
    validate_reward_rule_change,
    validate_reward_rule_deletion,
)

if TYPE_CHECKING:
    from app.vela.db.models import EarnRule, RewardRule


class CampaignAdmin(CanDeleteModelView):
    column_auto_select_related = True
    column_filters = ("retailerrewards.slug", "status")
    column_searchable_list = ("slug", "name")
    column_labels = dict(retailerrewards="Retailer")
    form_args = {
        "earn_inc_is_tx_value": {"validators": [validate_campaign_earn_inc_is_tx_value]},
        "status": {"validators": [validate_campaign_status_change]},
    }
    form_create_rules = ("retailerrewards", "name", "slug", "earn_inc_is_tx_value", "start_date", "end_date")

    # Be careful adding "inline_models = (EarnRule,)" here - the validate_earn_rule_increment
    # validator seemed to be bypassed in that view

    def delete_model(self, model: Campaign) -> bool:
        if not model.can_delete:
            flash("Only DRAFT campaigns can be deleted.", "error")
            return False
        return super().delete_model(model)

    def _flash_error_response(self, resp_json: Union[list, dict]) -> None:
        try:
            if isinstance(resp_json, list):
                for error in resp_json:
                    flash(
                        f"{error['display_message']} ::: {', '.join(error['campaigns'])}",
                        category="error",
                    )

            else:
                flash(resp_json["display_message"], category="error")
        except Exception as ex:
            if resp_json:
                msg = f"Unexpected response received: {resp_json}"
            else:
                msg = f"Unexpected response received: {resp_json}"
            flash(msg, category="error")
            logging.exception(msg, exc_info=ex)

    def _campaigns_status_change(self, campaigns_ids: list[str], status: str) -> None:
        campaign_slugs: list[str] = []
        retailer_slug: Optional[str] = None
        different_retailers = False

        for campaign_slug, campaign_retailer_slug in self.session.execute(
            select(Campaign.slug, RetailerRewards.slug).where(
                Campaign.id.in_([int(campaigns_id) for campaigns_id in campaigns_ids]),
                Campaign.retailer_id == RetailerRewards.id,
            )
        ).all():
            if retailer_slug is None:
                retailer_slug = campaign_retailer_slug

            elif retailer_slug != campaign_retailer_slug:
                different_retailers = True

            campaign_slugs.append(campaign_slug)

        if retailer_slug is None:
            raise ValueError(f"Unable to determine retailer for selected campaigns: {campaigns_ids}")

        if different_retailers is True:
            flash("All the selected campaigns must belong to the same retailer.", category="error")
        else:
            try:
                resp = requests.post(
                    f"{settings.VELA_BASE_URL}/bpl/rewards/{retailer_slug}/campaigns/status_change",
                    headers={"Authorization": f"token {settings.VELA_AUTH_TOKEN}"},
                    json={"requested_status": status, "campaign_slugs": campaign_slugs},
                )
                if 200 <= resp.status_code <= 204:
                    flash(f"Selected campaigns' status has been successfully changed to {status}")
                else:
                    self._flash_error_response(resp.json())

            except Exception as ex:
                msg = "Error: no response received."
                flash(msg, category="error")
                logging.exception(msg, exc_info=ex)

    @action(
        "activate campaigns",
        "Activate",
        "Selected campaigns must belong to the same Retailer, "
        "be in a DRAFT status and have one rewards rule and at least one earn rule.\n"
        "Are you sure you want to proceed?",
    )
    def action_activate_campaigns(self, ids: list[str]) -> None:
        self._campaigns_status_change(ids, "active")

    @action(
        "cancel campaigns",
        "Cancel",
        "Selected campaigns must belong to the same Retailer and be in a ACTIVE status.\n"
        "Are you sure you want to proceed?",
    )
    def action_cancel_campaigns(self, ids: list[str]) -> None:
        self._campaigns_status_change(ids, "cancelled")

    @action(
        "end campaigns",
        "End",
        "Selected campaigns must belong to the same Retailer and be in a ACTIVE status.\n"
        "Are you sure you want to proceed?",
    )
    def action_end_campaigns(self, ids: list[str]) -> None:
        self._campaigns_status_change(ids, "ended")


class EarnRuleAdmin(CanDeleteModelView):
    column_auto_select_related = True
    column_filters = ("campaign.name", "campaign.earn_inc_is_tx_value", "campaign.retailerrewards.slug")
    column_searchable_list = ("campaign.name",)
    column_list = (
        "campaign.name",
        "campaign.retailerrewards",
        "threshold",
        "campaign.earn_inc_is_tx_value",
        "increment",
        "increment_multiplier",
        "created_at",
        "updated_at",
    )
    column_labels = {
        "campaign.name": "Campaign",
        "campaign.retailerrewards": "Retailer",
        "campaign.earn_inc_is_tx_value": "Earn Inc. is Trans. Value?",
    }
    form_args = {
        "increment": {
            "validators": [validate_earn_rule_increment, wtforms.validators.NumberRange(min=1)],
            "description": (
                "How much the balance increases when an earn is triggered. Please enter the value "
                'multiplied by 100, e.g. for one stamp please enter "100" or for 15 points '
                'please enter "1500". Leave blank if the campaign is set to increment earns by the '
                "transaction value."
            ),
        },
        "threshold": {
            "validators": [wtforms.validators.NumberRange(min=1)],
            "description": (
                "Monetary value of a transaction required to trigger an earn. Please enter money value "
                'multiplied by 100, e.g. for £10.50, please enter "1050".'
            ),
        },
        "increment_multiplier": {"validators": [wtforms.validators.NumberRange(min=0)]},
    }
    column_type_formatters = typefmt.BASE_FORMATTERS | {type(None): lambda view, value: "-"}

    def on_model_delete(self, model: "EarnRule") -> None:
        validate_earn_rule_deletion(model.campaign_id)
        return super().on_model_delete(model)


class RewardRuleAdmin(CanDeleteModelView):
    column_auto_select_related = True
    column_filters = ("campaign.name", "campaign.retailerrewards.slug")
    column_searchable_list = ("campaign.name",)
    column_list = (
        "campaign.name",
        "campaign.retailerrewards",
        "reward_goal",
        "voucher_type_slug",
        "created_at",
        "updated_at",
    )
    column_labels = {
        "campaign.name": "Campaign",
        "campaign.retailerrewards": "Retailer",
    }
    form_args = {
        "reward_goal": {
            "validators": [wtforms.validators.NumberRange(min=1)],
            "description": (
                "Balance goal used to calculate if a voucher should be issued. "
                "This is a money value * 100, e.g. a reward goal of £10.50 should be 1050, "
                "and a reward goal of 8 stamps would be 800."
            ),
        },
        "voucher_type_slug": {
            "validators": [DataRequired(message="Slug is required"), wtforms.validators.Length(min=1, max=32)],
            "description": ("Used to determine what voucher on the till the Account holder will be allocated."),
        },
    }
    column_type_formatters = typefmt.BASE_FORMATTERS | {type(None): lambda view, value: "-"}

    def on_model_delete(self, model: "RewardRule") -> None:
        validate_reward_rule_deletion(model.campaign_id)
        return super().on_model_delete(model)

    def on_model_change(self, form: wtforms.Form, model: "RewardRule", is_created: bool) -> None:
        validate_reward_rule_change(model.campaign_id)
        return super().on_model_change(form, model, is_created)


class RetailerRewardsAdmin(BaseModelView):
    column_default_sort: Union[str, Tuple[str, bool]] = ("slug", False)


class TransactionAdmin(BaseModelView):
    column_filters = ("retailerrewards.slug",)
    column_searchable_list = ("transaction_id",)


class ProcessedTransactionAdmin(BaseModelView):
    column_filters = ("retailerrewards.slug",)
    column_searchable_list = ("transaction_id",)


class RetryTaskAdmin(BaseModelView, RetryTaskAdminBase):
    endpoint_prefix = settings.VELA_ENDPOINT_PREFIX
    redis = settings.redis


class TaskTypeAdmin(BaseModelView, TaskTypeAdminBase):
    pass


class TaskTypeKeyAdmin(BaseModelView, TaskTypeKeyAdminBase):
    pass


class TaskTypeKeyValueAdmin(BaseModelView, TaskTypeKeyValueAdminBase):
    pass
