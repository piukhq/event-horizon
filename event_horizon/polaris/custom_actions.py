import logging

from dataclasses import dataclass

from flask import flash
from sqlalchemy import func
from sqlalchemy.exc import DBAPIError
from sqlalchemy.future import select

from event_horizon.admin.utils import SessionDataMethodsMixin
from event_horizon.carina.db.models import Retailer
from event_horizon.carina.db.session import db_session as carina_db_session
from event_horizon.hubble.db.models import Activity
from event_horizon.hubble.db.session import db_session as hubble_db_session
from event_horizon.polaris.db.models import AccountHolder, AccountHolderReward, RetailerConfig
from event_horizon.polaris.db.session import db_session as polaris_db_session
from event_horizon.polaris.forms import DeleteRetailerActionForm
from event_horizon.vela.db.models import Campaign, RetailerRewards
from event_horizon.vela.db.session import db_session as vela_db_session


@dataclass
class SessionData(SessionDataMethodsMixin):
    retailer_name: str
    retailer_slug: str
    polaris_retailer_id: int
    retailer_status: str
    loyalty_name: str


class DeleteRetailerAction:
    logger = logging.getLogger("delete-retailer-action")

    def __init__(self) -> None:
        self.form = DeleteRetailerActionForm()
        self._session_data: SessionData | None = None

    @property
    def session_data(self) -> SessionData:
        if not self._session_data:
            raise ValueError("session_data is not set")

        return self._session_data

    @session_data.setter
    def session_data(self, value: str) -> None:
        self._session_data = SessionData.from_base64_str(value)

    def affected_account_holders_count(self) -> int:  # pragma: no cover
        return polaris_db_session.scalar(
            select(func.count(AccountHolder.id)).where(
                AccountHolder.retailer_id == self.session_data.polaris_retailer_id
            )
        )

    def affected_rewards_count(self) -> int:  # pragma: no cover
        return polaris_db_session.scalar(
            select(func.count(AccountHolderReward.id)).where(
                AccountHolderReward.account_holder_id == AccountHolder.id,
                AccountHolder.retailer_id == self.session_data.polaris_retailer_id,
            )
        )

    def affected_campaigns_slugs(self) -> list[str]:  # pragma: no cover
        return vela_db_session.scalars(
            select(Campaign.slug).where(
                Campaign.status == "ACTIVE",
                Campaign.retailer_id == RetailerRewards.id,
                RetailerRewards.slug == self.session_data.retailer_slug,
            )
        ).all()

    @staticmethod
    def _get_retailer_by_id(retailer_id: int) -> RetailerConfig:  # pragma: no cover
        return polaris_db_session.get(RetailerConfig, retailer_id)

    def validate_selected_ids(self, ids: list[str]) -> str | None:
        if not ids:
            return "no retailer selected."

        if len(ids) > 1:
            return "Only one Retailer allowed for this action"

        retailer = self._get_retailer_by_id(int(ids[0]))

        if retailer.status == "ACTIVE":
            return "Only non active Retailers allowed for this action"

        self._session_data = SessionData(
            retailer_name=retailer.name,
            retailer_slug=retailer.slug,
            polaris_retailer_id=retailer.id,
            retailer_status=retailer.status,
            loyalty_name=retailer.loyalty_name,
        )

        return None

    def _delete_polaris_retailer_data(self) -> None:  # pragma: no cover
        polaris_db_session.execute(
            RetailerConfig.__table__.delete().where(RetailerConfig.slug == self.session_data.retailer_slug)
        )
        polaris_db_session.flush()

    def _delete_vela_retailer_data(self) -> None:  # pragma: no cover
        vela_db_session.execute(
            RetailerRewards.__table__.delete().where(RetailerRewards.slug == self.session_data.retailer_slug)
        )
        vela_db_session.flush()

    def _delete_carina_retailer_data(self) -> None:  # pragma: no cover
        carina_db_session.execute(Retailer.__table__.delete().where(Retailer.slug == self.session_data.retailer_slug))
        carina_db_session.flush()

    def _delete_hubble_retailer_data(self) -> None:  # pragma: no cover
        hubble_db_session.execute(
            Activity.__table__.delete().where(Activity.retailer == self.session_data.retailer_slug)
        )
        hubble_db_session.flush()

    def delete_retailer(self) -> None:
        if not self.form.acceptance.data:
            flash("User did not agree to proceed, action halted.")
            return

        try:
            self._delete_polaris_retailer_data()
            self._delete_vela_retailer_data()
            self._delete_carina_retailer_data()
            self._delete_hubble_retailer_data()
        except DBAPIError:
            polaris_db_session.rollback()
            vela_db_session.rollback()
            carina_db_session.rollback()
            hubble_db_session.rollback()

            self.logger.exception(
                "Exception while trying to delete retailer %s (%d)",
                self.session_data.retailer_slug,
                self.session_data.polaris_retailer_id,
            )
            flash("Something went wrong, database changes rolled back", category="error")
            return

        polaris_db_session.commit()
        vela_db_session.commit()
        carina_db_session.commit()
        hubble_db_session.commit()
        flash(
            f"All rows related to retailer {self.session_data.retailer_name} ({self.session_data.polaris_retailer_id}) "
            "have been deleted."
        )
