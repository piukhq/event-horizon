from typing import TYPE_CHECKING

from sqlalchemy import MetaData, Table, create_engine
from sqlalchemy.orm import clear_mappers, mapper, sessionmaker
from sqlalchemy.pool import NullPool

from settings import POSTGRES_DSN

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

engine = create_engine(
    POSTGRES_DSN,
    poolclass=NullPool,
    echo=False,
)
SessionMaker = sessionmaker(bind=engine)


class User:
    pass


class MembershipCard:
    pass


class Voucher:
    pass


def load_session() -> "Session":
    clear_mappers()
    metadata = MetaData(engine)

    # map container class to relative table in the hermes database
    mapper(User, Table("user", metadata, autoload=True))
    mapper(MembershipCard, Table("membershipcard", metadata, autoload=True))
    mapper(Voucher, Table("voucher", metadata, autoload=True))

    return SessionMaker()
