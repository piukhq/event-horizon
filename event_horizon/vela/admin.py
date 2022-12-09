import logging

from dataclasses import dataclass
from datetime import datetime, timezone
from random import getrandbits
from typing import TYPE_CHECKING, Any

import requests
import wtforms

from cosmos_message_lib.schemas import ActivitySchema
from flask import flash, redirect, request, session, url_for
from flask_admin import expose
from flask_admin.actions import action
from flask_admin.model import typefmt
from retry_tasks_lib.admin.views import (
    RetryTaskAdminBase,
    TaskTypeAdminBase,
    TaskTypeKeyAdminBase,
    TaskTypeKeyValueAdminBase,
)
from sqlalchemy import inspect
from sqlalchemy.exc import DataError, IntegrityError
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from wtforms.validators import DataRequired

from event_horizon import settings
from event_horizon.activity_utils.enums import ActivityType
from event_horizon.activity_utils.tasks import sync_send_activity
from event_horizon.admin.model_views import BaseModelView, CanDeleteModelView
from event_horizon.vela.custom_actions import CampaignEndAction
from event_horizon.vela.db import Campaign, RetailerRewards, RewardRule
from event_horizon.vela.validators import (
    validate_campaign_end_date_change,
    validate_campaign_loyalty_type,
    validate_campaign_slug_update,
    validate_campaign_start_date_change,
    validate_campaign_status_change,
    validate_earn_rule_deletion,
    validate_earn_rule_increment,
    validate_earn_rule_max_amount,
    validate_increment_multiplier,
    validate_retailer_update,
    validate_reward_cap_for_loyalty_type,
    validate_reward_rule_allocation_window,
    validate_reward_rule_change,
    validate_reward_rule_deletion,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import SessionTransaction
    from werkzeug import Response

    from event_horizon.vela.db.models import EarnRule


@dataclass
class EasterEgg:
    greet: str
    content: str


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

    # Be careful adding "inline_models = (EarnRule,)" here - the validate_earn_rule_increment
    # validator seemed to be bypassed in that view

    def is_action_allowed(self, name: str) -> bool:
        if name == "delete":
            return False
        return super().is_action_allowed(name)

    def get_easter_egg(self) -> EasterEgg | None:
        try:
            first_name, *_ = self.sso_username.split(" ")
        except Exception:
            return None

        greet_msg = f"Hello there {first_name}"
        kitten_msg = "<img src='http://placekitten.com/200/300' alt='🐈 🐈‍⬛'>"
        profanities_msg = (
            "here's a list of profanities: "
            "<a href='https://en.wikipedia.org/wiki/Category:English_profanity'>profanities</a>"
        )

        match first_name.lower():
            case "francesco" | "susanne":
                return EasterEgg(greet_msg, kitten_msg)
            case "jess":
                return EasterEgg(greet_msg, profanities_msg)
            case "alyson":
                return EasterEgg(greet_msg, kitten_msg if getrandbits(1) else profanities_msg)
            case _:
                return EasterEgg(
                    greet_msg,
                    "<p>This is an internal tool with very little input validation.</p>"
                    "<p>¯\\_(ツ)_/¯</p>"
                    "<p>Please do try not to destroy everything.</p>",
                )

    @expose("/custom-actions/end-campaigns", methods=["GET", "POST"])
    def end_campaigns(self) -> "Response":

        if not self.user_info or self.user_session_expired:
            return redirect(url_for("auth_views.login"))

        campaigns_index_uri = url_for("vela/campaigns.index_view")
        if not self.can_edit:
            return redirect(campaigns_index_uri)

        cmp_end_action = CampaignEndAction(self.session)

        if "form_dynamic_val" in session and request.method == "POST":
            form_dynamic_val = session["form_dynamic_val"]

        else:
            selected_campaigns_ids: list[str] = request.args.to_dict(flat=False).get("ids", [])
            if not selected_campaigns_ids:
                flash("no campaign selected.", category="error")
                return redirect(campaigns_index_uri)

            try:
                cmp_end_action.validate_selected_campaigns(selected_campaigns_ids)
            except ValueError:
                return redirect(campaigns_index_uri)

            form_dynamic_val = cmp_end_action.session_form_data.to_base64_str()
            session["form_dynamic_val"] = form_dynamic_val

        cmp_end_action.update_form(form_dynamic_val)

        if cmp_end_action.form.validate_on_submit():
            del session["form_dynamic_val"]
            cmp_end_action.end_campaigns(self._campaigns_status_change, self.sso_username)
            return redirect(campaigns_index_uri)

        return self.render(
            "eh_end_campaign_action.html",
            active_campaign=cmp_end_action.session_form_data.active_campaign,
            draft_campaign=cmp_end_action.session_form_data.draft_campaign,
            form=cmp_end_action.form,
            easter_egg=self.get_easter_egg(),
        )

    def delete_model(self, model: Campaign) -> bool:
        if self.can_delete:
            retailer_slug = model.retailerrewards.slug
            campaign_slug = model.slug
            try:
                resp = requests.delete(
                    f"{settings.VELA_BASE_URL}/{retailer_slug}/campaigns/{campaign_slug}",
                    headers={"Authorization": f"token {settings.VELA_AUTH_TOKEN}"},
                    timeout=settings.REQUEST_TIMEOUT,
                )
                if not 200 <= resp.status_code <= 204:
                    flash("Could not complete this action. Please try again", category="error")
                    return False

            except Exception as ex:
                msg = "Error: no response received."
                flash(msg, category="error")
                logging.exception(msg, exc_info=ex)
                return False
            else:
                self.after_model_delete(model)
                return True
        else:
            flash("Only verified users can do this.", "error")
            return False

    def after_model_delete(self, model: Campaign) -> None:
        # Synchronously send activity for a campaign deletion after successful deletion
        activity_data = {}
        try:
            activity_data = ActivityType.get_campaign_deleted_activity_data(
                retailer_slug=model.retailerrewards.slug,
                campaign_name=model.name,
                sso_username=self.sso_username,
                activity_datetime=datetime.now(tz=timezone.utc),
                campaign_slug=model.slug,
                loyalty_type=model.loyalty_type,
                start_date=model.start_date,
                end_date=model.end_date,
            )
            sync_send_activity(
                activity_data,
                routing_key=ActivityType.CAMPAIGN.value,
            )
        except Exception as exc:
            logging.exception("Failed to publish CAMPAIGN (deleted) activity", exc_info=exc)

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
    ) -> bool:
        request_body: dict[str, Any] = {
            "requested_status": status,
            "campaign_slugs": campaign_slugs,
            "activity_metadata": {"sso_username": self.user_info["name"]},
        }

        # Change request body depending on action chosen
        if status == "ended" and issue_pending_rewards:
            request_body["issue_pending_rewards"] = issue_pending_rewards
        try:
            resp = requests.post(
                f"{settings.VELA_BASE_URL}/{retailer_slug}/campaigns/status_change",
                headers={"Authorization": f"token {settings.VELA_AUTH_TOKEN}"},
                json=request_body,
                timeout=settings.REQUEST_TIMEOUT,
            )
            if 200 <= resp.status_code <= 204:
                # Change success message depending on action chose for ending campaign
                if status == "ended":
                    for campaign_slug in campaign_slugs:
                        flash(self._get_flash_message(status, campaign_slug, issue_pending_rewards))
                else:
                    flash(f"Selected campaigns' status has been successfully changed to {status}")

                return True

            self._flash_error_response(resp.json())

        except Exception as ex:
            msg = "Error: no response received."
            flash(msg, category="error")
            logging.exception(msg, exc_info=ex)

        return False

    def _campaigns_status_change(
        self, campaigns_ids: list[int], status: str, issue_pending_rewards: bool | None = False
    ) -> bool:
        campaign_slugs: list[str] = []
        retailer_slug: str | None = None
        different_retailers = False

        for campaign_slug, campaign_retailer_slug in self.session.execute(
            select(Campaign.slug, RetailerRewards.slug).where(
                Campaign.id.in_(campaigns_ids),
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
            return False

        return self._send_campaign_status_change_request(retailer_slug, campaign_slugs, status, issue_pending_rewards)

    @action(
        "activate-campaigns",
        "Activate",
        "Selected campaigns must belong to the same Retailer, "
        "be in a DRAFT status and have one rewards rule and at least one earn rule.\n"
        "Are you sure you want to proceed?",
    )
    def action_activate_campaigns(self, ids: list[str]) -> None:
        if len(ids) > 1:
            flash("Cannot activate more than one campaign at once", category="error")
        else:
            self._campaigns_status_change([int(v) for v in ids], "active")

    @action(
        "cancel-campaigns",
        "Cancel",
        "Selected campaigns must belong to the same Retailer and be in a ACTIVE status.\n"
        "Are you sure you want to proceed?",
    )
    def action_cancel_campaigns(self, ids: list[str]) -> None:
        if len(ids) > 1:
            flash("Cannot cancel more than one campaign at once", category="error")
        else:
            self._campaigns_status_change([int(v) for v in ids], "cancelled")

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
            validate_retailer_update(
                old_retailer=form.retailerrewards.object_data,
                new_retailer=model.retailerrewards,
                campaign_status=model.status,
            )
            validate_campaign_slug_update(
                old_campaign_slug=form.slug.object_data, new_campaign_slug=model.slug, campaign_status=model.status
            )

        return super().on_model_change(form, model, is_created)

    def after_model_change(self, form: wtforms.Form, model: "Campaign", is_created: bool) -> None:

        if is_created:
            # Synchronously send activity for campaign creation after successfull campaign creation
            sync_send_activity(
                ActivityType.get_campaign_created_activity_data(
                    retailer_slug=model.retailerrewards.slug,
                    campaign_name=model.name,
                    sso_username=self.sso_username,
                    activity_datetime=datetime.now(tz=timezone.utc),
                    campaign_slug=model.slug,
                    loyalty_type=model.loyalty_type,
                    start_date=model.start_date,
                    end_date=model.end_date,
                ),
                routing_key=ActivityType.CAMPAIGN.value,
            )

        else:
            # Synchronously send activity for campaign update after successfull campaign update
            new_values: dict = {}
            original_values: dict = {}

            for field in form:
                # the campaign's retailer should not be editable but for now it is.
                # field.name != "retailerrewards" can be removed once BPL-744 is implemented.
                if field.name != "retailerrewards" and (new_val := getattr(model, field.name)) != field.object_data:
                    new_values[field.name] = new_val
                    original_values[field.name] = field.object_data

            if new_values:
                sync_send_activity(
                    ActivityType.get_campaign_updated_activity_data(
                        retailer_slug=model.retailerrewards.slug,
                        campaign_name=model.name,
                        sso_username=self.sso_username,
                        activity_datetime=model.updated_at,
                        campaign_slug=model.slug,
                        new_values=new_values,
                        original_values=original_values,
                    ),
                    routing_key=ActivityType.CAMPAIGN.value,
                )

    @action(
        "end-campaigns",
        "End",
        "The selected campaign must be in an ACTIVE state.\n"
        "An optional DRAFT campaign from the same retailer can be selected, "
        "this will automatically activate it and enable the transfer configuration for balances and pending rewards.\n"
        "You will be redirected to an action configuration page.\n"
        "Are you sure you want to proceed?",
    )
    def end_campaigns_action(self, ids: list[str]) -> "Response":
        return redirect(url_for("vela/campaigns.end_campaigns", ids=ids))

    def _send_cloned_campaign_activities(
        self, retailer_slug: str, campaign: Campaign, earn_rules: list["EarnRule"], reward_rules: list[RewardRule]
    ) -> None:
        sso_username = self.user_info["name"]
        campaign_slug = campaign.slug
        campaign_name = campaign.name
        loyalty_type = campaign.loyalty_type

        sync_send_activity(
            ActivityType.get_campaign_created_activity_data(
                retailer_slug=retailer_slug,
                campaign_name=campaign_name,
                sso_username=sso_username,
                activity_datetime=campaign.created_at,
                campaign_slug=campaign_slug,
                loyalty_type=loyalty_type,
                start_date=campaign.start_date,
                end_date=campaign.end_date,
            ),
            routing_key=ActivityType.CAMPAIGN.value,
        )
        sync_send_activity(
            (
                ActivitySchema(
                    **ActivityType.get_earn_rule_created_activity_data(
                        retailer_slug=retailer_slug,
                        campaign_name=campaign_name,
                        sso_username=sso_username,
                        activity_datetime=earn_rule.created_at,
                        campaign_slug=campaign_slug,
                        loyalty_type=loyalty_type,
                        threshold=earn_rule.threshold,
                        increment=earn_rule.increment,
                        increment_multiplier=earn_rule.increment_multiplier,
                        max_amount=earn_rule.max_amount,
                    )
                ).dict()
                for earn_rule in earn_rules
            ),
            routing_key=ActivityType.EARN_RULE.value,
        )
        sync_send_activity(
            (
                ActivitySchema(
                    **ActivityType.get_reward_rule_created_activity_data(
                        retailer_slug=retailer_slug,
                        campaign_name=campaign_name,
                        sso_username=sso_username,
                        activity_datetime=reward_rule.created_at,
                        campaign_slug=campaign_slug,
                        reward_slug=reward_rule.reward_slug,
                        reward_goal=reward_rule.reward_goal,
                        reward_cap=reward_rule.reward_cap,
                        refund_window=reward_rule.allocation_window,
                    )
                ).dict()
                for reward_rule in reward_rules
            ),
            routing_key=ActivityType.REWARD_RULE.value,
        )

    def _clone_campaign_and_rules_instances(self, campaign: Campaign) -> Campaign | None:
        def clone_instance(old_model_instance: Any) -> Any:

            mapper = inspect(type(old_model_instance))
            new_model_instance = type(old_model_instance)()

            for name, col in mapper.columns.items():

                if not (col.primary_key or col.unique or name in ["created_at", "updated_at"]):
                    setattr(new_model_instance, name, getattr(old_model_instance, name))

            return new_model_instance

        nested: "SessionTransaction"
        with self.session.begin_nested() as nested:

            error_msg: str | None = None
            new_slug = "CLONE_" + campaign.slug
            new_campaign = clone_instance(campaign)
            new_campaign.slug = new_slug
            new_campaign.status = "DRAFT"
            self.session.add(new_campaign)
            try:
                self.session.flush()
            except IntegrityError:
                error_msg = (
                    f"Another campaign with slug '{new_slug}' already exists, "
                    "please update it before trying to clone this campaign again."
                )

            except DataError:
                error_msg = f"Cloned campaign slug '{new_slug}' would exceed max slug length of 32 characters."

            if error_msg:
                nested.rollback()
                flash(error_msg, category="error")
                return None

            new_earn_rules: list["EarnRule"] = []
            for earn_rule in campaign.earnrule_collection:
                new_earn_rule = clone_instance(earn_rule)
                new_earn_rule.campaign_id = new_campaign.id
                new_earn_rules.append(new_earn_rule)
                self.session.add(new_earn_rule)

            new_reward_rules: list[RewardRule] = []
            for reward_rule in campaign.rewardrule_collection:
                new_reward_rule = clone_instance(reward_rule)
                new_reward_rule.campaign_id = new_campaign.id
                new_reward_rules.append(new_reward_rule)
                self.session.add(new_reward_rule)

            nested.commit()

        self.session.commit()
        self._send_cloned_campaign_activities(
            campaign.retailerrewards.slug,
            new_campaign,
            new_earn_rules,
            new_reward_rules,
        )
        return new_campaign

    @action(
        "clone-campaign",
        "Clone",
        "Only one campaign allowed for this action, the selected campaign's retailer must be in a TEST state.",
    )
    def clone_campaign_action(self, ids: list[str]) -> None:
        if len(ids) > 1:
            flash("Only one campaign at a time is supported for this action.", category="error")
            return

        campaign = (
            self.session.execute(
                select(Campaign)
                .options(
                    joinedload(Campaign.rewardrule_collection),
                    joinedload(Campaign.earnrule_collection),
                    joinedload(Campaign.retailerrewards),
                )
                .where(Campaign.id == ids[0])
            )
            .unique()
            .scalar_one()
        )

        if campaign.retailerrewards.status != "TEST":
            flash("The campaign's retailer status must be TEST.", category="error")
            return

        new_campaign = self._clone_campaign_and_rules_instances(campaign)
        if new_campaign:
            flash(
                "Successfully cloned campaign, reward rules, and earn rules from campaign: "
                f"{campaign.slug} (id {campaign.id}) to campaign {new_campaign.slug} (id {new_campaign.id})."
            )


class EarnRuleAdmin(CanDeleteModelView):
    column_auto_select_related = True
    column_filters = ("campaign.name", "campaign.slug", "campaign.loyalty_type", "campaign.retailerrewards.slug")
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
                "Leave blank for accumulator campaigns. For stamp, this is the number to be awarded per eligible "
                "transaction multiplied by 100. 100 = 1 stamp."
            ),
        },
        "threshold": {
            "validators": [wtforms.validators.NumberRange(min=0)],
            "description": ("Minimum transaction value for earn in pence. E.g. for £10.50, please enter '1050'."),
        },
        "increment_multiplier": {"validators": [validate_increment_multiplier, wtforms.validators.NumberRange(min=0)]},
        "max_amount": {
            "validators": [validate_earn_rule_max_amount, wtforms.validators.NumberRange(min=0)],
            "description": ("Upper limit for transaction earn in pence. 0 for stamp."),
        },
    }
    column_type_formatters = typefmt.BASE_FORMATTERS | {type(None): lambda view, value: "-"}

    def on_model_delete(self, model: "EarnRule") -> None:
        validate_earn_rule_deletion(model.campaign_id)

        # Synchronously send activity for an earn rule deletion after successful deletion
        sync_send_activity(
            ActivityType.get_earn_rule_deleted_activity_data(
                retailer_slug=model.campaign.retailerrewards.slug,
                campaign_name=model.campaign.name,
                sso_username=self.sso_username,
                activity_datetime=datetime.now(tz=timezone.utc),
                campaign_slug=model.campaign.slug,
                threshold=model.threshold,
                increment=model.increment,
                increment_multiplier=model.increment_multiplier,
                max_amount=model.max_amount,
            ),
            routing_key=ActivityType.EARN_RULE.value,
        )

        return super().on_model_delete(model)

    def after_model_change(self, form: wtforms.Form, model: "EarnRule", is_created: bool) -> None:
        if is_created:
            # Synchronously send activity for earn rule creation after successful creation
            sync_send_activity(
                ActivityType.get_earn_rule_created_activity_data(
                    retailer_slug=model.campaign.retailerrewards.slug,
                    campaign_name=model.campaign.name,
                    sso_username=self.sso_username,
                    activity_datetime=model.created_at,
                    campaign_slug=model.campaign.slug,
                    loyalty_type=model.campaign.loyalty_type,
                    threshold=model.threshold,
                    increment=model.increment,
                    increment_multiplier=model.increment_multiplier,
                    max_amount=model.max_amount,
                ),
                routing_key=ActivityType.EARN_RULE.value,
            )
        else:
            # Synchronously send activity for an earn rule update after successful update
            new_values: dict = {}
            original_values: dict = {}

            for field in form:
                # the campaign's retailer should not be editable but for now it is.
                # field.name != "retailerrewards" can be removed once BPL-744 is implemented.
                if field.name != "retailerrewards" and (new_val := getattr(model, field.name)) != field.object_data:
                    new_values[field.name] = new_val
                    original_values[field.name] = field.object_data

            if new_values:
                sync_send_activity(
                    ActivityType.get_earn_rule_updated_activity_data(
                        retailer_slug=model.campaign.retailerrewards.slug,
                        campaign_name=model.campaign.name,
                        sso_username=self.sso_username,
                        activity_datetime=model.updated_at,
                        campaign_slug=model.campaign.slug,
                        new_values=new_values,
                        original_values=original_values,
                    ),
                    routing_key=ActivityType.EARN_RULE.value,
                )


class RewardRuleAdmin(CanDeleteModelView):
    column_auto_select_related = True
    column_filters = ("campaign.name", "campaign.slug", "campaign.retailerrewards.slug")
    column_searchable_list = ("campaign.name",)
    column_list = (
        "campaign.name",
        "campaign.retailerrewards",
        "reward_goal",
        "reward_slug",
        "allocation_window",
        "reward_cap",
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
        "reward_cap": {
            "default": None,
            "validators": [validate_reward_cap_for_loyalty_type],
            "blank_text": "None",
            "description": ("Transaction reward cap. Accumulator campaigns only."),
        },
    }
    column_type_formatters = typefmt.BASE_FORMATTERS | {type(None): lambda view, value: "-"}

    def on_model_delete(self, model: "RewardRule") -> None:
        validate_reward_rule_deletion(model.campaign_id)
        # Synchronously send activity for an earn rule deletion after successful deletion
        sync_send_activity(
            ActivityType.get_reward_rule_deleted_activity_data(
                retailer_slug=model.campaign.retailerrewards.slug,
                campaign_name=model.campaign.name,
                sso_username=self.sso_username,
                activity_datetime=datetime.now(tz=timezone.utc),
                campaign_slug=model.campaign.slug,
                reward_slug=model.reward_slug,
                reward_goal=model.reward_goal,
                refund_window=model.allocation_window,
                reward_cap=model.reward_cap,
            ),
            routing_key=ActivityType.REWARD_RULE.value,
        )
        return super().on_model_delete(model)

    def on_model_change(self, form: wtforms.Form, model: "RewardRule", is_created: bool) -> None:
        validate_reward_rule_change(model.campaign, is_created)
        return super().on_model_change(form, model, is_created)

    def after_model_change(self, form: wtforms.Form, model: "RewardRule", is_created: bool) -> None:

        if is_created:
            # Synchronously send activity for reward rule creation after successful creation
            sync_send_activity(
                ActivityType.get_reward_rule_created_activity_data(
                    retailer_slug=model.campaign.retailerrewards.slug,
                    campaign_name=model.campaign.name,
                    sso_username=self.sso_username,
                    activity_datetime=model.created_at,
                    campaign_slug=model.campaign.slug,
                    reward_goal=model.reward_goal,
                    refund_window=model.allocation_window,
                    reward_slug=model.reward_slug,
                    reward_cap=model.reward_cap,
                ),
                routing_key=ActivityType.REWARD_RULE.value,
            )

        else:
            new_values: dict = {}
            original_values: dict = {}

            for field in form:
                if (new_val := getattr(model, field.name)) != field.object_data:
                    if field.name == "campaign":
                        new_values["campaign_slug"] = new_val.slug
                        original_values["campaign_slug"] = field.object_data.slug
                    else:
                        new_values[field.name] = new_val
                        original_values[field.name] = field.object_data
            # Synchronously send activity for reward rule update after successful update
            sync_send_activity(
                ActivityType.get_reward_rule_updated_activity_data(
                    retailer_slug=model.campaign.retailerrewards.slug,
                    campaign_name=model.campaign.name,
                    sso_username=self.sso_username,
                    activity_datetime=model.updated_at,
                    campaign_slug=model.campaign.slug,
                    new_values=new_values,
                    original_values=original_values,
                ),
                routing_key=ActivityType.REWARD_RULE.value,
            )


class RetailerRewardsAdmin(BaseModelView):
    can_create = False
    can_edit = False
    column_default_sort = ("slug", False)
    column_searchable_list = ("slug",)
    column_filters = ("status",)


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
