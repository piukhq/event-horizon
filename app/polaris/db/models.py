from sqlalchemy.ext.automap import automap_base
from sqlalchemy.sql.schema import MetaData

from app.polaris.db.session import engine

metadata = MetaData()
Base = automap_base(metadata=metadata)


class AccountHolder(Base):  # type: ignore
    __tablename__ = "account_holder"

    def __str__(self) -> str:
        return self.id


class AccountHolderProfile(Base):  # type: ignore
    __tablename__ = "account_holder_profile"

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"


class Retailer(Base):  # type: ignore
    __tablename__ = "retailer"

    def __str__(self) -> str:
        return f"{self.name} ({self.slug})"


Base.prepare(engine, reflect=True)
