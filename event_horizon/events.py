from typing import Type

from sqlalchemy import event

from event_horizon.carina.db import Retailer
from event_horizon.carina.db import db_session as carina_db_session
from event_horizon.polaris.db import RetailerConfig
from event_horizon.vela.db import RetailerRewards
from event_horizon.vela.db import db_session as vela_db_session


# pylint: disable=unused-argument
def sync_retailer_insert(mapper: Type[RetailerConfig], connection: str, target: RetailerConfig) -> None:
    vela_db_session.add(RetailerRewards(slug=target.slug, status=target.status))
    vela_db_session.commit()
    carina_db_session.add(Retailer(slug=target.slug, status=target.status))
    carina_db_session.commit()


# pylint: disable=unused-argument
def sync_retailer_delete(mapper: Type[RetailerConfig], connection: str, target: RetailerConfig) -> None:
    vela_db_session.query(RetailerRewards).filter_by(slug=target.slug).delete()
    vela_db_session.commit()
    carina_db_session.query(Retailer).filter_by(slug=target.slug).delete()
    carina_db_session.commit()


def init_events() -> None:
    event.listen(RetailerConfig, "after_insert", sync_retailer_insert)
    event.listen(RetailerConfig, "before_delete", sync_retailer_delete)
