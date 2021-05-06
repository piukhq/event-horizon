from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.scoping import scoped_session
from sqlalchemy.pool import NullPool

from app.settings import POLARIS_DATABASE_URI

engine = create_engine(POLARIS_DATABASE_URI, poolclass=NullPool)
db_session = scoped_session(sessionmaker(bind=engine))
