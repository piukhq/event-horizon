import inspect
from typing import TYPE_CHECKING

from sqlalchemy import MetaData, Table, create_engine
from sqlalchemy.orm import clear_mappers, mapper, sessionmaker
from sqlalchemy.pool import NullPool

from app.db import models
from settings import SQLALCHEMY_DATABASE_URI

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

models_loaded = False
engine = create_engine(SQLALCHEMY_DATABASE_URI, poolclass=NullPool, echo=False)
SessionMaker = sessionmaker(bind=engine)


def _load_models() -> None:
    clear_mappers()
    metadata = MetaData(engine)

    for name, obj in inspect.getmembers(models):
        if inspect.isclass(obj):
            mapper(obj, Table(name.lower(), metadata, autoload=True))


def get_db_session() -> "Session":
    global models_loaded

    if not models_loaded:
        _load_models()
        models_loaded = True

    return SessionMaker()
