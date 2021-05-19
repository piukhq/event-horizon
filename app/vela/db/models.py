from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import MetaData

from app.db import UpdatedAtMixin

metadata = MetaData()
Base = automap_base(metadata=metadata)


class RetailerRewards(Base):  # type: ignore
    __tablename__ = "retailer_rewards"

    def __str__(self) -> str:
        return self.slug


class Campaign(Base, UpdatedAtMixin):  # type: ignore
    __tablename__ = "campaign"

    retailer = relationship("RetailerRewards")

    def __str__(self) -> str:
        return self.name


class EarnRule(Base, UpdatedAtMixin):  # type: ignore
    __tablename__ = "earn_rule"
