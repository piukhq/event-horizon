from sqlalchemy.ext.automap import AutomapBase, automap_base
from sqlalchemy.sql.schema import MetaData

from app.db import UpdatedAtMixin

metadata = MetaData()
Base: AutomapBase = automap_base(metadata=metadata)


class RewardConfig(Base, UpdatedAtMixin):
    __tablename__ = "reward_config"

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.retailer_slug}, " f"{self.reward_slug}, {self.validity_days})"


class Reward(Base, UpdatedAtMixin):
    __tablename__ = "reward"

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.retailer_slug}, " f"{self.code}, {self.allocated})"


class RewardUpdate(Base, UpdatedAtMixin):
    __tablename__ = "reward_update"

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.id})"
