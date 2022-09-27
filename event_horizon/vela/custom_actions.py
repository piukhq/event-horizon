import base64
import pickle

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Callable

from flask import flash
from sqlalchemy.future import select

from event_horizon.polaris.utils import balance_transfer
from event_horizon.vela.db.models import Campaign, RewardRule
from event_horizon.vela.forms import EndCampaignActionForm

if TYPE_CHECKING:  # pragma: no cover
    from sqlalchemy.engine import Row
    from sqlalchemy.orm import Session


@dataclass
class CampaignRow:
    id: int  # pylint: disable=invalid-name
    slug: str
    type: str


@dataclass
class SessionFormData:
    active_campaigns: list[CampaignRow]
    draft_campaign: CampaignRow | None
    transfer_balance_from_choices: list[tuple[int, str]]
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
    form_optional_fields = ["transfer_balance", "transfer_balance_from", "convert_rate", "qualify_threshold"]

    def __init__(self, db_session: "Session") -> None:
        self.db_session = db_session
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
    def _get_and_validate_campaigns(campaign_rows: list) -> tuple[list[CampaignRow], CampaignRow | None, list[str]]:
        errors: list[str] = []
        active_campaigns = [
            CampaignRow(cmp.id, cmp.slug, cmp.loyalty_type) for cmp in campaign_rows if cmp.status == "ACTIVE"
        ]
        try:
            draft_campaign, *extra = [
                CampaignRow(cmp.id, cmp.slug, cmp.loyalty_type) for cmp in campaign_rows if cmp.status == "DRAFT"
            ]
        except ValueError:
            draft_campaign = None
            extra = []

        if not active_campaigns:
            errors.append("At least one ACTIVE campaign must be provided.")

        if extra:
            errors.append("Only up to one DRAFT campaign allowed.")

        return active_campaigns, draft_campaign, errors

    @staticmethod
    def _check_retailer_and_status(campaign_rows: list["Row"]) -> list[str]:
        errors: list[str] = []

        if not campaign_rows:
            errors.append("No campaign found.")

        if not all(cmp.retailer_id == campaign_rows[0].retailer_id for cmp in campaign_rows):
            errors.append("Selected campaigns must belong to the same retailer")

        if any(cmp.status not in ["ACTIVE", "DRAFT"] for cmp in campaign_rows):
            errors.append("Only ACTIVE or DRAFT campaigns allowed for this action.")

        return errors

    # this is a separate method to allow for easy mocking
    def _get_campaign_rows(self, selected_campaigns_ids: list[str]) -> list["Row"]:  # pragma: no cover
        return self.db_session.execute(
            select(Campaign.id, Campaign.slug, Campaign.loyalty_type, Campaign.status, Campaign.retailer_id).where(
                Campaign.id.in_([int(campaigns_id) for campaigns_id in selected_campaigns_ids]),
            )
        ).all()

    def validate_selected_campaigns(self, selected_campaigns_ids: list[str]) -> None:
        campaign_rows = self._get_campaign_rows(selected_campaigns_ids)
        errors = self._check_retailer_and_status(campaign_rows)
        active_campaigns, draft_campaign, other_errors = self._get_and_validate_campaigns(campaign_rows)

        errors += other_errors
        if errors:
            for error in errors:
                flash(error, category="error")

            raise ValueError("failed validation")

        transfer_balance_from_choices = [
            (cmp.id, cmp.slug) for cmp in active_campaigns if draft_campaign and cmp.type == draft_campaign.type
        ]
        self._session_form_data = SessionFormData(
            active_campaigns=active_campaigns,
            draft_campaign=draft_campaign,
            transfer_balance_from_choices=transfer_balance_from_choices,
            optional_fields_needed=bool(draft_campaign and transfer_balance_from_choices),
        )

    def update_form(self, form_dynamic_values: str) -> None:
        if not self._session_form_data:
            self._session_form_data = SessionFormData.from_base64_str(form_dynamic_values)

        self.form.transfer_balance_from.choices = self._session_form_data.transfer_balance_from_choices
        if not self._session_form_data.optional_fields_needed:
            for field_name in self.form_optional_fields:
                delattr(self.form, field_name)

    # this is a separate method to allow for easy mocking
    def _get_from_campaign_slug_and_goal(self, from_campaign_id: int) -> tuple[str, int] | None:  # pragma: no cover
        return self.db_session.execute(
            select(Campaign.slug, RewardRule.reward_goal)
            .select_from(RewardRule)
            .join(Campaign)
            .where(Campaign.id == from_campaign_id)
        ).first()

    def _transfer_balance(
        self, from_campaign_id: int, to_campaign: CampaignRow, rate_percent: int, threshold: int
    ) -> None:
        res = self._get_from_campaign_slug_and_goal(from_campaign_id)
        if not res:
            raise ValueError(
                f"Could not find Campaign.slug and RewardRule.reward_goal for campaign of id: {from_campaign_id}"
            )

        from_campaign_slug, goal = res
        min_balance = int((goal / 100) * threshold)
        balance_transfer(
            from_campaign_slug=from_campaign_slug,
            to_campaign_slug=to_campaign.slug,
            min_balance=min_balance,
            rate_percent=rate_percent,
            loyalty_type=to_campaign.type,
        )
        flash(
            f"Balance transferred from campaign '{from_campaign_slug}' to campaign '{to_campaign.slug}' "
            f"with a {rate_percent}% rate for balances of at least {min_balance}"
        )

    # this is a separate method to allow for easy mocking
    def _update_from_campaign_end_date(self) -> None:  # pragma: no cover
        self.db_session.execute(
            Campaign.__table__.update()
            .values(end_date=datetime.now(tz=timezone.utc))
            .where(Campaign.id == self.form.transfer_balance_from.data)
        )
        self.db_session.commit()

    def end_campaigns(self, status_change_fn: Callable) -> None:
        success = True
        transfer_balance_requested = self.form.transfer_balance and self.form.transfer_balance.data

        if transfer_balance_requested and not self.session_form_data.draft_campaign:
            raise ValueError("unexpected: no draft campaign found")

        if self.session_form_data.draft_campaign:
            success = status_change_fn([self.session_form_data.draft_campaign.id], "active")
            if success and transfer_balance_requested:
                self._update_from_campaign_end_date()
                self._transfer_balance(
                    from_campaign_id=self.form.transfer_balance_from.data,
                    to_campaign=self.session_form_data.draft_campaign,
                    rate_percent=self.form.convert_rate.data,
                    threshold=self.form.qualify_threshold.data,
                )

        if success:
            status_change_fn(
                [cmp.id for cmp in self.session_form_data.active_campaigns],
                "ended",
                issue_pending_rewards=self.form.convert_pending_rewards.data,
            )
