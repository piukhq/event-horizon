from sqlalchemy.ext.automap import automap_base
from sqlalchemy.sql.schema import MetaData

from app.db import UpdatedAtMixin

metadata = MetaData()
Base = automap_base(metadata=metadata)


class VoucherConfig(Base, UpdatedAtMixin):  # type: ignore
    __tablename__ = "voucher_config"
