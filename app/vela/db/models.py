from sqlalchemy import Column, DateTime, text
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

    updated_at = Column(
        DateTime,
        server_default=text("TIMEZONE('utc', CURRENT_TIMESTAMP)"),
        onupdate=text("TIMEZONE('utc', CURRENT_TIMESTAMP)"),
        nullable=False,
    )

    def __str__(self) -> str:
        return self.name


Base.prepare(engine, reflect=True)
