import logging
from collections.abc import Callable, Generator
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TYPE_CHECKING, cast

from flask import flash
from sqlalchemy.future import select

from event_horizon.activity_utils.enums import ActivityType
from event_horizon.activity_utils.tasks import sync_send_activity
from event_horizon.admin.utils import SessionDataMethodsMixin
from event_horizon.polaris.db import db_session as polaris_db_session
from event_horizon.polaris.utils import transfer_balance, transfer_pending_rewards
from event_horizon.vela.db.models import Campaign, RetailerRewards, RewardRule
from event_horizon.vela.enums import PendingRewardChoices
from event_horizon.vela.forms import EndCampaignActionForm

if TYPE_CHECKING:  # pragma: no cover
    from sqlalchemy.engine import Row
    from sqlalchemy.orm import Session, SessionTransaction


@dataclass
class CampaignRow:
    id: int
    slug: str
    type: str
    reward_goal: int
    reward_slug: str


@dataclass
class SessionFormData(SessionDataMethodsMixin):
    retailer_slug: str
    active_campaign: CampaignRow
    draft_campaign: CampaignRow | None
    optional_fields_needed: bool


@dataclass
class ActivityData:
    type: ActivityType
    payload: dict
    error_message: str


class CampaignEndAction:
    logger = logging.getLogger("campaign-end-action")
    form_optional_fields = ["transfer_balance", "convert_rate", "qualify_threshold"]

    def __init__(self, db_session: "Session") -> None:
        self.vela_db_session = db_session
        self.form = EndCampaignActionForm()
        self._session_form_data: SessionFormData | None = None

    @property
    def session_form_data(self) -> SessionFormData:
        if not self._session_form_data:
            raise ValueError(
                "validate_selected_campaigns or update_form must be called before accessing session_form_data"
            )

        return self._session_form_data

    @staticmethod
    def _get_and_validate_campaigns(campaign_rows: list) -> tuple[CampaignRow | None, CampaignRow | None, list[str]]:
        errors: list[str] = []
        try:
            active_campaign, *extra_active = (
                CampaignRow(cmp.id, cmp.slug, cmp.loyalty_type, cmp.reward_goal, cmp.reward_slug)
                for cmp in campaign_rows
                if cmp.status == "ACTIVE"
            )
        except ValueError:
            active_campaign = None
            extra_active = []

        try:
            draft_campaign, *extra_draft = (
                CampaignRow(cmp.id, cmp.slug, cmp.loyalty_type, cmp.reward_goal, cmp.reward_slug)
                for cmp in campaign_rows
                if cmp.status == "DRAFT"
            )
        except ValueError:
            draft_campaign = None
            extra_draft = []

        if not active_campaign:
            errors.append("One ACTIVE campaign must be provided.")

        if extra_active or extra_draft:
            errors.append("Only up to one DRAFT and one ACTIVE campaign allowed.")

        return active_campaign, draft_campaign, errors

    @staticmethod
    def _get_retailer_and_check_status(campaign_rows: list["Row"]) -> list[str]:
        errors: list[str] = []

        if not campaign_rows:
            errors.append("No campaign found.")

        if any(cmp.status not in ("ACTIVE", "DRAFT") for cmp in campaign_rows):
            errors.append("Only ACTIVE or DRAFT campaigns allowed for this action.")

        if not all(cmp.retailer_slug == campaign_rows[0].retailer_slug for cmp in campaign_rows):
            errors.append("Selected campaigns must belong to the same retailer.")

        if not all(cmp.loyalty_type == campaign_rows[0].loyalty_type for cmp in campaign_rows):
            errors.append("Selected campaigns must have the same loyalty type.")

        return errors

    # this is a separate method to allow for easy mocking
    def _get_campaign_rows(self, selected_campaigns_ids: list[str]) -> list["Row"]:  # pragma: no cover
        return self.vela_db_session.execute(
            select(
                Campaign.id,
                Campaign.slug,
                Campaign.loyalty_type,
                Campaign.status,
                RewardRule.reward_goal,
                RewardRule.reward_slug,
                RetailerRewards.slug.label("retailer_slug"),
            )
            .select_from(RewardRule)
            .join(Campaign)
            .join(RetailerRewards)
            .where(
                Campaign.id.in_([int(campaigns_id) for campaigns_id in selected_campaigns_ids]),
            )
        ).all()

    def validate_selected_campaigns(self, selected_campaigns_ids: list[str]) -> None:
        campaign_rows = self._get_campaign_rows(selected_campaigns_ids)
        errors = self._get_retailer_and_check_status(campaign_rows)
        active_campaign, draft_campaign, other_errors = self._get_and_validate_campaigns(campaign_rows)
        errors += other_errors

        if errors or active_campaign is None:
            for error in errors:
                flash(error, category="error")

            raise ValueError("failed validation")

        self._session_form_data = SessionFormData(
            retailer_slug=campaign_rows[0].retailer_slug,
            active_campaign=active_campaign,
            draft_campaign=draft_campaign,
            optional_fields_needed=draft_campaign is not None,
        )

    def update_form(self, form_dynamic_values: str) -> None:
        if not self._session_form_data:
            self._session_form_data = SessionFormData.from_base64_str(form_dynamic_values)

        self.form.handle_pending_rewards.choices = PendingRewardChoices.get_choices(
            self._session_form_data.optional_fields_needed
        )
        if not self._session_form_data.optional_fields_needed:
            for field_name in self.form_optional_fields:
                delattr(self.form, field_name)

    def _transfer_balance_and_pending_rewards(
        self,
        *,
        retailer_slug: str,
        from_campaign: CampaignRow,
        to_campaign: CampaignRow,
        to_campaign_start_date: datetime,
        rate_percent: int,
        threshold: int,
        transfer_balance_requested: bool,
        transfer_pending_rewards_requested: bool,
    ) -> None:
        pending_rewards_transfer_activity_payloads: Generator[dict, None, None] | None = None
        balance_change_activity_payloads: Generator[dict, None, None] | None = None
        msg = f"Transfer from campaign '{from_campaign.slug}' to campaign '{to_campaign.slug}'."

        # start a session savepoint to ensure all polaris changes are either successful or rolled back.
        savepoint: "SessionTransaction"
        with polaris_db_session.begin_nested() as savepoint:
            if transfer_pending_rewards_requested:
                msg += "\n Pending Rewards transferred."
                pending_rewards_transfer_activity_payloads = transfer_pending_rewards(
                    polaris_db_session,
                    retailer_slug=retailer_slug,
                    from_campaign_slug=from_campaign.slug,
                    to_campaign_slug=to_campaign.slug,
                    to_campaign_reward_slug=to_campaign.reward_slug,
                    to_campaign_start_date=to_campaign_start_date,
                )

            if transfer_balance_requested:
                min_balance = int((from_campaign.reward_goal / 100) * threshold)
                msg += f"\n Balance transferred with a {rate_percent}% rate for balances of at least {min_balance}."
                balance_change_activity_payloads = transfer_balance(
                    polaris_db_session,
                    retailer_slug=retailer_slug,
                    from_campaign_slug=from_campaign.slug,
                    to_campaign_slug=to_campaign.slug,
                    to_campaign_start_date=to_campaign_start_date,
                    min_balance=min_balance,
                    rate_percent=rate_percent,
                    loyalty_type=to_campaign.type,
                )

            savepoint.commit()

        if pending_rewards_transfer_activity_payloads:
            sync_send_activity(pending_rewards_transfer_activity_payloads, routing_key=ActivityType.REWARD_STATUS.value)

        if balance_change_activity_payloads:
            sync_send_activity(balance_change_activity_payloads, routing_key=ActivityType.BALANCE_CHANGE.value)

        polaris_db_session.commit()
        flash(msg)

    # this is a separate method to allow for easy mocking
    def _update_from_campaign_end_date(self) -> None:  # pragma: no cover
        self.vela_db_session.execute(
            Campaign.__table__.update()
            .values(end_date=datetime.now(tz=timezone.utc))
            .where(Campaign.id == self.session_form_data.active_campaign.id)
        )
        self.vela_db_session.commit()

    def _get_campaign_start_date_by_id(self, campaign_id: int) -> datetime:
        return self.vela_db_session.execute(select(Campaign.start_date).where(Campaign.id == campaign_id)).scalar_one()

    def _handle_send_activity(self, success: bool, activity_data: ActivityData) -> None:
        if success:
            sync_send_activity(activity_data.payload, routing_key=activity_data.type.value)
        else:
            self.logger.error(
                "%s\n%s payload: \n%s", activity_data.error_message, activity_data.type.name, activity_data.payload
            )
            flash(activity_data.error_message, category="error")

    def end_campaigns(self, status_change_fn: Callable, sso_username: str) -> None:
        activity_start_dt = datetime.now(tz=timezone.utc)
        campaign_migration_activity: ActivityData | None = None
        success = True
        transfer_balance_requested = self.form.transfer_balance and self.form.transfer_balance.data
        transfer_pending_rewards_requested, issue_pending_rewards = cast(
            PendingRewardChoices, self.form.handle_pending_rewards.data
        ).get_strategy()
        transfer_requested = transfer_balance_requested or transfer_pending_rewards_requested

        if not self.session_form_data.draft_campaign and transfer_requested:
            raise ValueError("unexpected: no draft campaign found")

        if self.session_form_data.draft_campaign:
            success = status_change_fn([self.session_form_data.draft_campaign.id], "active")

            if success and transfer_requested:
                to_campaign_start_date = self._get_campaign_start_date_by_id(self.session_form_data.draft_campaign.id)
                self._update_from_campaign_end_date()
                self._transfer_balance_and_pending_rewards(
                    retailer_slug=self.session_form_data.retailer_slug,
                    from_campaign=self.session_form_data.active_campaign,
                    to_campaign=self.session_form_data.draft_campaign,
                    to_campaign_start_date=to_campaign_start_date,
                    rate_percent=self.form.convert_rate.data,
                    threshold=self.form.qualify_threshold.data,
                    transfer_balance_requested=transfer_balance_requested,
                    transfer_pending_rewards_requested=transfer_pending_rewards_requested,
                )

                campaign_migration_activity = ActivityData(
                    type=ActivityType.CAMPAIGN_MIGRATION,
                    payload=ActivityType.get_campaign_migration_activity_data(
                        retailer_slug=self.session_form_data.retailer_slug,
                        from_campaign_slug=self.session_form_data.active_campaign.slug,
                        to_campaign_slug=self.session_form_data.draft_campaign.slug,
                        sso_username=sso_username,
                        activity_datetime=activity_start_dt,
                        balance_conversion_rate=self.form.convert_rate.data,
                        qualify_threshold=self.form.qualify_threshold.data,
                        pending_rewards=self.form.handle_pending_rewards.data,
                        transfer_balance_requested=transfer_balance_requested,
                    ),
                    error_message=(
                        "Balance migrated successfully but failed to end the active campaign"
                        f" {self.session_form_data.active_campaign.slug}."
                    ),
                )

        if success:
            success = status_change_fn(
                [self.session_form_data.active_campaign.id],
                "ended",
                issue_pending_rewards=issue_pending_rewards,
            )

        if campaign_migration_activity:
            self._handle_send_activity(success, campaign_migration_activity)
