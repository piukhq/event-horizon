import base64
import pickle

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Callable, cast

from flask import flash
from sqlalchemy.future import select

from event_horizon.polaris.db import db_session as polaris_db_session
from event_horizon.polaris.utils import transfer_balance, transfer_pending_rewards
from event_horizon.vela.db.models import Campaign, RewardRule
from event_horizon.vela.enums import PendingRewardChoices
from event_horizon.vela.forms import EndCampaignActionForm

if TYPE_CHECKING:  # pragma: no cover
    from sqlalchemy.engine import Row
    from sqlalchemy.orm import Session, SessionTransaction


@dataclass
class CampaignRow:
    id: int  # pylint: disable=invalid-name
    slug: str
    type: str
    reward_goal: int
    reward_slug: str


@dataclass
class SessionFormData:
    active_campaign: CampaignRow
    draft_campaign: CampaignRow | None
    optional_fields_needed: bool

    def to_base64_str(self) -> str:
        return base64.b64encode(pickle.dumps(self)).decode()

    @classmethod
    def from_base64_str(cls, form_dynamic_values: str) -> "SessionFormData":
        try:
            session_form_data = pickle.loads(base64.b64decode(form_dynamic_values.encode()))
        except Exception as ex:
            raise ValueError("unexpected value found for 'form_dynamic_values'") from ex

        if not isinstance(session_form_data, cls):
            raise TypeError(f"'form_dynamic_values' is not a valid {cls.__name__}")

        return session_form_data


class CampaignEndAction:
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
            active_campaign, *extra_active = [
                CampaignRow(cmp.id, cmp.slug, cmp.loyalty_type, cmp.reward_goal, cmp.reward_slug)
                for cmp in campaign_rows
                if cmp.status == "ACTIVE"
            ]
        except ValueError:
            active_campaign = None
            extra_active = []

        try:
            draft_campaign, *extra_draft = [
                CampaignRow(cmp.id, cmp.slug, cmp.loyalty_type, cmp.reward_goal, cmp.reward_slug)
                for cmp in campaign_rows
                if cmp.status == "DRAFT"
            ]
        except ValueError:
            draft_campaign = None
            extra_draft = []

        if not active_campaign:
            errors.append("One ACTIVE campaign must be provided.")

        if extra_active or extra_draft:
            errors.append("Only up to one DRAFT and one ACTIVE campaign allowed.")

        return active_campaign, draft_campaign, errors

    @staticmethod
    def _check_retailer_and_status(campaign_rows: list["Row"]) -> list[str]:
        errors: list[str] = []

        if not campaign_rows:
            errors.append("No campaign found.")

        if any(cmp.status not in ["ACTIVE", "DRAFT"] for cmp in campaign_rows):
            errors.append("Only ACTIVE or DRAFT campaigns allowed for this action.")

        if not all(cmp.retailer_id == campaign_rows[0].retailer_id for cmp in campaign_rows):
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
                Campaign.retailer_id,
                RewardRule.reward_goal,
                RewardRule.reward_slug,
            )
            .select_from(RewardRule)
            .join(Campaign)
            .where(
                Campaign.id.in_([int(campaigns_id) for campaigns_id in selected_campaigns_ids]),
            )
        ).all()

    def validate_selected_campaigns(self, selected_campaigns_ids: list[str]) -> None:
        campaign_rows = self._get_campaign_rows(selected_campaigns_ids)
        errors = self._check_retailer_and_status(campaign_rows)
        active_campaign, draft_campaign, other_errors = self._get_and_validate_campaigns(campaign_rows)
        errors += other_errors

        if errors or active_campaign is None:
            for error in errors:
                flash(error, category="error")

            raise ValueError("failed validation")

        self._session_form_data = SessionFormData(
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
        from_campaign: CampaignRow,
        to_campaign: CampaignRow,
        rate_percent: int,
        threshold: int,
        transfer_balance_requested: bool,
        transfer_pending_rewards_requested: bool,
    ) -> None:

        msg = f"Transfer from campaign '{from_campaign.slug}' to campaign '{to_campaign.slug}'."

        # start a session savepoint to ensure all polaris changes are either successful or rolled back.
        savepoint: "SessionTransaction"
        with polaris_db_session.begin_nested() as savepoint:

            if transfer_pending_rewards_requested:
                msg += "\n Pending Rewards transferred."
                transfer_pending_rewards(
                    polaris_db_session,
                    from_campaign_slug=from_campaign.slug,
                    to_campaign_slug=to_campaign.slug,
                    to_campaign_reward_slug=to_campaign.reward_slug,
                )

            if transfer_balance_requested:
                min_balance = int((from_campaign.reward_goal / 100) * threshold)
                msg += f"\n Balance transferred with a {rate_percent}% rate for balances of at least {min_balance}."
                transfer_balance(
                    polaris_db_session,
                    from_campaign_slug=from_campaign.slug,
                    to_campaign_slug=to_campaign.slug,
                    min_balance=min_balance,
                    rate_percent=rate_percent,
                    loyalty_type=to_campaign.type,
                )

            savepoint.commit()

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

    def end_campaigns(self, status_change_fn: Callable) -> None:
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
                self._update_from_campaign_end_date()
                self._transfer_balance_and_pending_rewards(
                    from_campaign=self.session_form_data.active_campaign,
                    to_campaign=self.session_form_data.draft_campaign,
                    rate_percent=self.form.convert_rate.data,
                    threshold=self.form.qualify_threshold.data,
                    transfer_balance_requested=transfer_balance_requested,
                    transfer_pending_rewards_requested=transfer_pending_rewards_requested,
                )

        if success:
            status_change_fn(
                [self.session_form_data.active_campaign.id],
                "ended",
                issue_pending_rewards=issue_pending_rewards,
            )
