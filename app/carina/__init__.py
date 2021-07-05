from typing import TYPE_CHECKING

from .admin import VoucherConfigAdmin
from .db import VoucherConfig, db_session

if TYPE_CHECKING:
    from flask_admin import Admin


def register_carina_admin(event_horizon_admin: "Admin") -> None:
    carina_menu_title = "Voucher Management"
    event_horizon_admin.add_view(
        VoucherConfigAdmin(
            VoucherConfig, db_session, "Voucher Configurations", endpoint="voucher-config", category=carina_menu_title
        )
    )
