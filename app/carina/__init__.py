from typing import TYPE_CHECKING

from .admin import VoucherAdmin, VoucherAllocationAdmin, VoucherConfigAdmin
from .db import Voucher, VoucherAllocation, VoucherConfig, db_session

if TYPE_CHECKING:
    from flask_admin import Admin


def register_carina_admin(event_horizon_admin: "Admin") -> None:
    carina_menu_title = "Voucher Management"
    event_horizon_admin.add_view(
        VoucherConfigAdmin(
            VoucherConfig, db_session, "Voucher Configurations", endpoint="voucher-configs", category=carina_menu_title
        )
    )
    event_horizon_admin.add_view(
        VoucherAdmin(Voucher, db_session, "Vouchers", endpoint="vouchers", category=carina_menu_title)
    )
    event_horizon_admin.add_view(
        VoucherAllocationAdmin(
            VoucherAllocation,
            db_session,
            "Voucher Allocations",
            endpoint="voucher-allocations",
            category=carina_menu_title,
        )
    )
