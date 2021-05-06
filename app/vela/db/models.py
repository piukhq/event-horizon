from datetime import datetime

from sqlalchemy import Column, DateTime, func
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.sql.schema import MetaData

from app.vela.db.session import engine

metadata = MetaData()
Base = automap_base(metadata=metadata)


class RetailerRewards(Base):  # type: ignore
    __tablename__ = "retailer_rewards"

    def __str__(self) -> str:
        return self.slug


class Campaign(Base):  # type: ignore
    __tablename__ = "campaign"

    updated_at = Column(DateTime, server_default=func.now(), onupdate=datetime.utcnow(), nullable=False)

    def __str__(self) -> str:
        return self.name


Base.prepare(engine, reflect=True)
