from sqlalchemy.ext.automap import automap_base

from app.db.session import engine

Base = automap_base()


class Retailer(Base):  # type: ignore
    __tablename__ = "retailer"

    def __str__(self) -> str:
        return self.name


Base.prepare(engine, reflect=True)

# get models from Base mapping
AccountHolder = Base.classes.account_holder
AccountHolderProfile = Base.classes.account_holder_profile
