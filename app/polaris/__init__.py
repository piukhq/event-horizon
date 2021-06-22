from typing import TYPE_CHECKING

from .admin import AccountHolderActivationAdmin, AccountHolderAdmin, AccountHolderProfileAdmin, RetailerConfigAdmin
from .db import AccountHolder, AccountHolderActivation, AccountHolderProfile, RetailerConfig, db_session

if TYPE_CHECKING:
    from flask_admin import Admin


def register_polaris_admin(event_horizon_admin: "Admin") -> None:
    polaris_menu_title = "Customer Management"
    event_horizon_admin.add_view(
        AccountHolderAdmin(
            AccountHolder, db_session, "Account Holders", endpoint="account-holders", category=polaris_menu_title
        )
    )
    event_horizon_admin.add_view(
        AccountHolderProfileAdmin(
            AccountHolderProfile, db_session, "Profiles", endpoint="profiles", category=polaris_menu_title
        )
    )
    event_horizon_admin.add_view(
        AccountHolderActivationAdmin(
            AccountHolderActivation,
            db_session,
            "Account Holder Activations",
            endpoint="account-holder-activations",
            category=polaris_menu_title,
        )
    )
    event_horizon_admin.add_view(
        RetailerConfigAdmin(
            RetailerConfig, db_session, "Retailers' Config", endpoint="retailers-config", category=polaris_menu_title
        )
    )
