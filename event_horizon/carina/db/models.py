from sqlalchemy.ext.automap import AutomapBase, automap_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import MetaData

from event_horizon.db import UpdatedAtMixin

metadata = MetaData()
Base: AutomapBase = automap_base(metadata=metadata)


class Retailer(Base, UpdatedAtMixin):
    __tablename__ = "retailer"

    fetch_types = relationship("FetchType", back_populates="retailers", secondary="retailer_fetch_type")
    retailerfetchtype_collection = relationship(
        "RetailerFetchType", back_populates="retailer", overlaps="fetch_types,retailers"
    )

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.slug})"

    def __str__(self) -> str:
        return self.slug


class FetchType(Base, UpdatedAtMixin):
    __tablename__ = "fetch_type"

    retailers = relationship(
        "Retailer",
        back_populates="fetch_types",
        secondary="retailer_fetch_type",
        overlaps="retailerfetchtype_collection",
    )
    retailerfetchtype_collection = relationship(
        "RetailerFetchType", back_populates="fetchtype", overlaps="fetch_types,retailers"
    )

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name})"

    def __str__(self) -> str:
        return self.name


class RetailerFetchType(Base, UpdatedAtMixin):
    __tablename__ = "retailer_fetch_type"

    retailer = relationship("Retailer", back_populates="retailerfetchtype_collection", overlaps="fetch_types,retailers")
    fetchtype = relationship(
        "FetchType", back_populates="retailerfetchtype_collection", overlaps="fetch_types,retailers"
    )

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


class RewardCampaign(Base, UpdatedAtMixin):
    __tablename__ = "reward_campaign"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.id})"


class RewardFileLog(Base, UpdatedAtMixin):
    __tablename__ = "reward_file_log"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.id})"
