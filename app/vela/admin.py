import logging

from typing import TYPE_CHECKING, Any

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
from app.vela.db import Campaign, RetailerRewards, RewardRule
from app.vela.validators import (
    validate_campaign_end_date_change,
    validate_campaign_loyalty_type,
    validate_campaign_start_date_change,
    validate_campaign_status_change,
    validate_earn_rule_deletion,
    validate_earn_rule_increment,
    validate_earn_rule_max_amount,
    validate_reward_rule_allocation_window,
    validate_reward_rule_change,
    validate_reward_rule_deletion,
)

if TYPE_CHECKING:
    from app.vela.db.models import EarnRule


class CampaignAdmin(CanDeleteModelView):
    column_auto_select_related = True
    action_disallowed_list = ["delete"]
    column_filters = ("retailerrewards.slug", "status")
    column_searchable_list = ("slug", "name")
    column_labels = {"retailerrewards": "Retailer"}
    form_args = {
        "loyalty_type": {"validators": [DataRequired(), validate_campaign_loyalty_type]},
        "status": {"validators": [validate_campaign_status_change]},
    }
    form_create_rules = form_edit_rules = (
        "retailerrewards",
        "name",
        "slug",
        "loyalty_type",
        "start_date",
        "end_date",
    )

    def is_action_allowed(self, name: str) -> bool:
        if name == "delete":
            return False
        return super().is_action_allowed(name)

    # Be careful adding "inline_models = (EarnRule,)" here - the validate_earn_rule_increment
    # validator seemed to be bypassed in that view

    def delete_model(self, model: Campaign) -> None:
        if self.can_delete:
            retailer_slug = model.retailerrewards.slug
            campaign_slug = model.slug
            try:
                resp = requests.delete(
                    f"{settings.VELA_BASE_URL}/{retailer_slug}/campaigns/{campaign_slug}",
                    headers={"Authorization": f"token {settings.VELA_AUTH_TOKEN}"},
                )
                if 200 <= resp.status_code <= 204:
                    # Change success message depending on action chose for ending campaign
                    flash("Selected campaign has been successfully deleted.")
                else:
                    flash("Could not complete this action. Please try again", category="error")

            except Exception as ex:
                msg = "Error: no response received."
                flash(msg, category="error")
                logging.exception(msg, exc_info=ex)
        else:
            flash("Only verified users can do this.", "error")

    def _check_for_refund_window(self, campaign_slug: str) -> bool:
        allocation_window = (
            self.session.execute(
                select(RewardRule.allocation_window).where(
                    Campaign.slug == campaign_slug,
                    Campaign.retailer_id == RetailerRewards.id,
                    RewardRule.campaign_id == Campaign.id,
                )
            )
            .scalars()
            .first()
        )
        return allocation_window

    def _get_flash_message(self, status: str, campaign_slug: str, issue_pending_rewards: bool | None = False) -> str:
        pending_rewards_action = "deleted"
        if issue_pending_rewards:
            pending_rewards_action = "converted"

        flash_message = f"""Selected campaigns' status has been successfully changed to {status} and pending
                            rewards were {pending_rewards_action}"""

        refund_window = self._check_for_refund_window(campaign_slug)
        if refund_window == 0:
            flash_message = f"""Campaign {campaign_slug} was ended but it was not configured for
                                pending rewards"""
        return flash_message

    def _send_campaign_status_change_request(
        self, retailer_slug: str, campaign_slugs: list[str], status: str, issue_pending_rewards: bool | None = False
    ) -> None:
        request_body: dict[str, Any] = {"requested_status": status, "campaign_slugs": campaign_slugs}

        # Change request body depending on action chosen
        if status == "ended" and issue_pending_rewards:
            request_body["issue_pending_rewards"] = issue_pending_rewards
        try:
            resp = requests.post(
                f"{settings.VELA_BASE_URL}/{retailer_slug}/campaigns/status_change",
                headers={"Authorization": f"token {settings.VELA_AUTH_TOKEN}"},
                json=request_body,
            )
            if 200 <= resp.status_code <= 204:
                # Change success message depending on action chose for ending campaign
                if status == "ended":
                    for campaign_slug in campaign_slugs:
                        flash(self._get_flash_message(status, campaign_slug, issue_pending_rewards))
                else:
                    flash(f"Selected campaigns' status has been successfully changed to {status}")
            else:
                self._flash_error_response(resp.json())

        except Exception as ex:
            msg = "Error: no response received."
            flash(msg, category="error")
            logging.exception(msg, exc_info=ex)

    def _campaigns_status_change(
        self, campaigns_ids: list[str], status: str, issue_pending_rewards: bool | None = False
    ) -> None:
        campaign_slugs: list[str] = []
        retailer_slug: str | None = None
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
        elif issue_pending_rewards:
            self._send_campaign_status_change_request(retailer_slug, campaign_slugs, status, issue_pending_rewards)
        else:
            self._send_campaign_status_change_request(retailer_slug, campaign_slugs, status)

    @action(
        "activate-campaigns",
        "Activate",
        "Selected campaigns must belong to the same Retailer, "
        "be in a DRAFT status and have one rewards rule and at least one earn rule.\n"
        "Are you sure you want to proceed?",
    )
    def action_activate_campaigns(self, ids: list[str]) -> None:
        self._campaigns_status_change(ids, "active")

    @action(
        "cancel-campaigns",
        "Cancel",
        "Selected campaigns must belong to the same Retailer and be in a ACTIVE status.\n"
        "Are you sure you want to proceed?",
    )
    def action_cancel_campaigns(self, ids: list[str]) -> None:
        self._campaigns_status_change(ids, "cancelled")

    @action(
        "end-campaigns-convert-pending-rewards",
        "End (and Convert pending rewards)",
        "Selected campaigns must belong to the same Retailer and be in a ACTIVE status.\n"
        "If the campaign has a refund window and pending rewards, they will be CONVERTED.\n"
        "Are you sure you want to proceed?",
    )
    def action_end_campaigns_and_convert_pending_rewards(self, ids: list[str]) -> None:
        self._campaigns_status_change(ids, "ended", issue_pending_rewards=True)

    @action(
        "end-campaigns-delete-pending-rewards",
        "End (and Delete pending rewards)",
        "Selected campaigns must belong to the same Retailer and be in a ACTIVE status.\n"
        "If the campaign has a refund window and pending rewards, they will be DELETED.\n"
        "Are you sure you want to proceed?",
    )
    def action_end_campaigns_and_delete_pending_rewards(self, ids: list[str]) -> None:
        self._campaigns_status_change(ids, "ended")

    def on_model_change(self, form: wtforms.Form, model: "Campaign", is_created: bool) -> None:
        if not is_created:
            validate_campaign_end_date_change(
                old_end_date=form.end_date.object_data,
                new_end_date=model.end_date,
                status=model.status,
                start_date=model.start_date,
            )
            validate_campaign_start_date_change(
                old_start_date=form.start_date.object_data, new_start_date=model.start_date, status=model.status
            )
        return super().on_model_change(form, model, is_created)


class EarnRuleAdmin(CanDeleteModelView):
    column_auto_select_related = True
    column_filters = ("campaign.name", "campaign.loyalty_type", "campaign.retailerrewards.slug")
    column_searchable_list = ("campaign.name",)
    column_list = (
        "campaign.name",
        "campaign.retailerrewards",
        "threshold",
        "campaign.loyalty_type",
        "increment",
        "increment_multiplier",
        "created_at",
        "updated_at",
        "max_amount",
    )
    column_labels = {
        "campaign.name": "Campaign",
        "campaign.retailerrewards": "Retailer",
        "campaign.loyalty_type": "LoyaltyType",
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
            "validators": [wtforms.validators.NumberRange(min=0)],
            "description": (
                "Monetary value of a transaction required to trigger an earn. Please enter money value "
                'multiplied by 100, e.g. for £10.50, please enter "1050".'
            ),
        },
        "increment_multiplier": {"validators": [wtforms.validators.NumberRange(min=0)]},
        "max_amount": {
            "validators": [validate_earn_rule_max_amount, wtforms.validators.NumberRange(min=0)],
            "description": ("Can only be set if the campaign's loyalty type is ACCUMULATOR"),
        },
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
        "reward_slug",
        "allocation_window",
        "created_at",
        "updated_at",
    )
    column_labels = {
        "campaign.name": "Campaign",
        "campaign.retailerrewards": "Retailer",
        "allocation_window": "Refund Window",
    }
    form_args = {
        "reward_goal": {
            "validators": [wtforms.validators.NumberRange(min=1)],
            "description": (
                "Balance goal used to calculate if a reward should be issued. "
                "This is a money value * 100, e.g. a reward goal of £10.50 should be 1050, "
                "and a reward goal of 8 stamps would be 800."
            ),
        },
        "reward_slug": {
            "validators": [DataRequired(message="Slug is required"), wtforms.validators.Length(min=1, max=32)],
            "description": ("Used to determine what reward on the till the Account holder will be allocated."),
        },
        "allocation_window": {
            "default": 0,
            "validators": [validate_reward_rule_allocation_window, wtforms.validators.NumberRange(min=0)],
            "description": (
                "Period of time before a reward is allocated to an AccountHolder in days."
                " Accumulator campaigns only."
            ),
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
    column_default_sort = ("slug", False)


class RetailerStoreAdmin(BaseModelView):
    column_labels = {"retailerrewards": "Retailer"}
    column_filters = ("retailerrewards.slug", "created_at")
    column_searchable_list = ("store_name", "mid")

    form_args = {
        "store_name": {
            "validators": [DataRequired(message="Store name is required")],
        },
        "mid": {
            "validators": [DataRequired(message="MID is required")],
        },
    }


class TransactionAdmin(BaseModelView):
    column_filters = ("retailerrewards.slug", "created_at", "datetime")
    column_searchable_list = ("transaction_id", "account_holder_uuid")


class ProcessedTransactionAdmin(BaseModelView):
    column_filters = ("retailerrewards.slug", "created_at", "datetime")
    column_searchable_list = ("transaction_id", "payment_transaction_id", "account_holder_uuid")


class RetryTaskAdmin(BaseModelView, RetryTaskAdminBase):
    endpoint_prefix = settings.VELA_ENDPOINT_PREFIX
    redis = settings.redis


class TaskTypeAdmin(BaseModelView, TaskTypeAdminBase):
    pass


class TaskTypeKeyAdmin(BaseModelView, TaskTypeKeyAdminBase):
    pass


class TaskTypeKeyValueAdmin(BaseModelView, TaskTypeKeyValueAdminBase):
    pass
