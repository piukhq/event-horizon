from retry_tasks_lib.db.models import load_models_to_metadata
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.sql.schema import MetaData

from app.db import UpdatedAtMixin

metadata = MetaData()
load_models_to_metadata(metadata)
Base = automap_base(metadata=metadata)


class VoucherConfig(Base, UpdatedAtMixin):  # type: ignore
    __tablename__ = "voucher_config"

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.retailer_slug}, " f"{self.voucher_type_slug}, {self.validity_days})"


class Voucher(Base, UpdatedAtMixin):  # type: ignore
    __tablename__ = "voucher"

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.retailer_slug}, " f"{self.voucher_code}, {self.allocated})"


class VoucherUpdate(Base, UpdatedAtMixin):  # type: ignore
    __tablename__ = "voucher_update"

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.id})"
