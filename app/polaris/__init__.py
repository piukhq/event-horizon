from typing import TYPE_CHECKING

from .admin import AccountHolderAdmin, AccountHolderProfileAdmin, EnrolmentCallbackAdmin, RetailerConfigAdmin
from .db import AccountHolder, AccountHolderProfile, EnrolmentCallback, RetailerConfig, db_session

if TYPE_CHECKING:
    from flask_admin import Admin


def register_polaris_admin(event_horizon_admin: "Admin") -> None:
    event_horizon_admin.add_view(
        AccountHolderAdmin(AccountHolder, db_session, "Account Holders", endpoint="account-holders")
    )
    event_horizon_admin.add_view(
        AccountHolderProfileAdmin(AccountHolderProfile, db_session, "Profiles", endpoint="profiles")
    )
    event_horizon_admin.add_view(
        RetailerConfigAdmin(RetailerConfig, db_session, "Retailers' Config", endpoint="retailers-config")
    )
    event_horizon_admin.add_view(
        EnrolmentCallbackAdmin(EnrolmentCallback, db_session, "Enrolment Callbacks", endpoint="enrolment-callbacks")
    )
