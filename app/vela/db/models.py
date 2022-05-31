from sqlalchemy.ext.automap import AutomapBase, automap_base
from sqlalchemy.sql.schema import MetaData

from app.db import UpdatedAtMixin

metadata = MetaData()
Base: AutomapBase = automap_base(metadata=metadata)


class RetailerRewards(Base):
    __tablename__ = "retailer_rewards"

    def __repr__(self) -> str:
        return self.slug


class RetailerStore(Base, UpdatedAtMixin):
    __tablename__ = "retailer_store"

    def __repr__(self) -> str:
        return self.name


class Campaign(Base, UpdatedAtMixin):
    __tablename__ = "campaign"

    def __repr__(self) -> str:
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

    def __repr__(self) -> str:
        return self.transaction_id
