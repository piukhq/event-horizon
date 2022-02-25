from typing import Type

from sqlalchemy import event

from app.carina.db import Retailer
from app.carina.db import db_session as carina_db_session
from app.polaris.db import RetailerConfig
from app.vela.db import RetailerRewards
from app.vela.db import db_session as vela_db_session


def sync_retailer_insert(mapper: Type[RetailerConfig], connection: str, target: RetailerConfig) -> None:
    vela_db_session.add(RetailerRewards(slug=target.slug))
    vela_db_session.commit()
    carina_db_session.add(Retailer(slug=target.slug))
    carina_db_session.commit()


def sync_retailer_delete(mapper: Type[RetailerConfig], connection: str, target: RetailerConfig) -> None:
    vela_db_session.query(RetailerRewards).filter_by(slug=target.slug).delete()
    vela_db_session.commit()
    carina_db_session.query(Retailer).filter_by(slug=target.slug).delete()
    carina_db_session.commit()


event.listen(RetailerConfig, "after_insert", sync_retailer_insert)
event.listen(RetailerConfig, "before_delete", sync_retailer_delete)
