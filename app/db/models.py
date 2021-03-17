from datetime import datetime

from sqlalchemy import Column, DateTime
from sqlalchemy.ext.automap import automap_base

from app.db.session import engine

Base = automap_base()


class Merchant(Base):
    __tablename__ = "merchant"
    created_at = Column(DateTime, default=datetime.now)

    def __str__(self):
        return self.name


class User(Base):
    __tablename__ = "user"
    created_at = Column(DateTime, default=datetime.now)


Base.prepare(engine, reflect=True)

# get models from Base mapping
UserProfile = Base.classes.userprofile
