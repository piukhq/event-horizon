from sqlalchemy.ext.automap import AutomapBase, automap_base
from sqlalchemy.sql.schema import MetaData

from app.db import UpdatedAtMixin

metadata = MetaData()
Base: AutomapBase = automap_base(metadata=metadata)


class RetailerRewards(Base):
    __tablename__ = "retailer_rewards"

    def __str__(self) -> str:
        return self.slug


class Campaign(Base, UpdatedAtMixin):
    __tablename__ = "campaign"

    def __str__(self) -> str:
        return f"{self.name} - {self.status} ({self.retailerrewards.slug})"

    @property
    def can_delete(self) -> bool:
        return self.status == "DRAFT"


class EarnRule(Base, UpdatedAtMixin):
    __tablename__ = "earn_rule"


class RewardRule(Base, UpdatedAtMixin):
    __tablename__ = "reward_rule"


class Transaction(Base, UpdatedAtMixin):
    __tablename__ = "transaction"


class ProcessedTransaction(Base, UpdatedAtMixin):
    __tablename__ = "processed_transaction"

    def __str__(self) -> str:
        return self.transaction_id
