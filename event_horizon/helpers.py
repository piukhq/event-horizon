from event_horizon.carina.db import Retailer
from event_horizon.carina.db import db_session as carina_db_session
from event_horizon.vela.db import RetailerRewards
from event_horizon.vela.db import db_session as vela_db_session


def sync_retailer_insert(retailer_slug: str, retailer_status: str) -> None:
    vela_db_session.add(RetailerRewards(slug=retailer_slug, status=retailer_status))
    vela_db_session.commit()
    carina_db_session.add(Retailer(slug=retailer_slug, status=retailer_status))
    carina_db_session.commit()
