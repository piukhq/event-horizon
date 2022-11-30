from sqlalchemy.future import select

from event_horizon.carina.db import Retailer
from event_horizon.carina.db import db_session as carina_db_session
from event_horizon.vela.db import Campaign, RetailerRewards
from event_horizon.vela.db import db_session as vela_db_session


def sync_retailer_insert(retailer_slug: str, retailer_status: str) -> None:
    vela_db_session.add(RetailerRewards(slug=retailer_slug, status=retailer_status))
    vela_db_session.commit()
    carina_db_session.add(Retailer(slug=retailer_slug, status=retailer_status))
    carina_db_session.commit()


def check_activate_campaign_for_retailer(retailer_id: int) -> list[int]:
    return (
        vela_db_session.execute(
            select(Campaign.id).where(Campaign.retailer_id == retailer_id, Campaign.status == "ACTIVE")
        )
        .scalars()
        .all()
    )


def sync_activate_retailer(retailer_id: int) -> None:
    try:
        carina_db_session.execute(Retailer.__table__.update().values(status="ACTIVE").where(Retailer.id == retailer_id))
        carina_db_session.commit()
        vela_db_session.execute(
            RetailerRewards.__table__.update().values(status="ACTIVE").where(RetailerRewards.id == retailer_id)
        )
        vela_db_session.commit()
    except Exception as ex:
        carina_db_session.rollback()
        vela_db_session.rollback()
        raise ex
