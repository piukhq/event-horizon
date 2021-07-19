from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import MetaData

from app.db import UpdatedAtMixin

metadata = MetaData()
Base = automap_base(metadata=metadata)


class VoucherRetailer(Base):  # type: ignore
    __tablename__ = "voucher_retailer"

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.retailer_slug}"


class VoucherConfig(Base, UpdatedAtMixin):  # type: ignore
    __tablename__ = "voucher_config"

    voucher_collection = relationship("Voucher", backref="vouchers", cascade="all, delete-orphan")

    def __str__(self) -> str:
        return (
            f"{self.__class__.__name__}({self.voucherretailer.retailer_slug}, "
            f"{self.voucher_type_slug}, {self.validity_days})"
        )


class Voucher(Base, UpdatedAtMixin):  # type: ignore
    __tablename__ = "voucher"
