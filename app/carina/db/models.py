from sqlalchemy.ext.automap import AutomapBase, automap_base
from sqlalchemy.sql.schema import MetaData

from app.db import UpdatedAtMixin

metadata = MetaData()
Base: AutomapBase = automap_base(metadata=metadata)


class Retailer(Base, UpdatedAtMixin):
    __tablename__ = "retailer"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.slug})"

    def __str__(self) -> str:
        return self.slug


class FetchType(Base, UpdatedAtMixin):
    __tablename__ = "fetch_type"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name})"

    def __str__(self) -> str:
        return self.name


class RetailerFetchType(Base, UpdatedAtMixin):
    __tablename__ = "retailer_fetch_type"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.retailer.slug}, {self.fetchtype.name})"


class RewardConfig(Base, UpdatedAtMixin):
    __tablename__ = "reward_config"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.retailer.slug}, " f"{self.reward_slug}, {self.validity_days})"


class Reward(Base, UpdatedAtMixin):
    __tablename__ = "reward"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.retailer.slug}, " f"{self.code}, {self.allocated})"


class RewardUpdate(Base, UpdatedAtMixin):
    __tablename__ = "reward_update"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.id})"
