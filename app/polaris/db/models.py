from sqlalchemy.ext.automap import automap_base
from sqlalchemy.sql.schema import MetaData

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


class EnrolmentCallback(Base):  # type: ignore
    __tablename__ = "enrolment_callback"


class RetailerConfig(Base):  # type: ignore
    __tablename__ = "retailer_config"

    def __str__(self) -> str:
        return f"{self.name} ({self.slug})"
