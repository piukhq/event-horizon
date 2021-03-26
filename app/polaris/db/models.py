from sqlalchemy.ext.automap import automap_base
from sqlalchemy.sql.schema import MetaData

from app.polaris.db.session import engine

metadata = MetaData()
Base = automap_base(metadata=metadata)


class Retailer(Base):  # type: ignore
    __tablename__ = "retailer"

    def __str__(self) -> str:
        return self.name


Base.prepare(engine, reflect=True)

# get models from Base mapping
AccountHolder = Base.classes.account_holder
AccountHolderProfile = Base.classes.account_holder_profile
