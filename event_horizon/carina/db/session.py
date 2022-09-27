from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.pool import NullPool

from event_horizon.settings import CARINA_DATABASE_URI

engine = create_engine(CARINA_DATABASE_URI, poolclass=NullPool)
db_session = scoped_session(sessionmaker(bind=engine))
