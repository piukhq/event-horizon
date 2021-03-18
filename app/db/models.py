from datetime import datetime

from sqlalchemy import Column, DateTime, Integer
from sqlalchemy.ext.automap import automap_base

from app.db.session import engine

Base = automap_base()


class Retailer(Base):  # type: ignore
    __tablename__ = "retailer"
    created_at = Column(DateTime, default=datetime.now)
    card_number_length = Column(Integer, default=10)

    def __str__(self) -> str:
        return self.name


class AccountHolder(Base):  # type: ignore
    __tablename__ = "account_holder"
    created_at = Column(DateTime, default=datetime.now)


Base.prepare(engine, reflect=True)

# get models from Base mapping
AccountHolderProfile = Base.classes.account_holder_profile
