from sqlalchemy.ext.automap import automap_base
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

    def __str__(self) -> str:
        return self.name


class EarnRule(Base, UpdatedAtMixin):  # type: ignore
    __tablename__ = "earn_rule"


class RewardRule(Base, UpdatedAtMixin):  # type: ignore
    __tablename__ = "reward_rule"


class Transaction(Base, UpdatedAtMixin):  # type: ignore
    __tablename__ = "transaction"


class ProcessedTransaction(Base, UpdatedAtMixin):  # type: ignore
    __tablename__ = "processed_transaction"
