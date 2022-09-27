from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.pool import NullPool

from event_horizon.settings import HUBBLE_DATABASE_URI

engine = create_engine(HUBBLE_DATABASE_URI, poolclass=NullPool)
SyncSessionMaker = sessionmaker(bind=engine, future=True, expire_on_commit=False)
db_session = scoped_session(SyncSessionMaker)
