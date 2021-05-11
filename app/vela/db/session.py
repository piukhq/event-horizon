from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.pool import NullPool

from app.settings import VELA_DATABASE_URI

engine = create_engine(VELA_DATABASE_URI, poolclass=NullPool)
db_session = scoped_session(sessionmaker(bind=engine))
