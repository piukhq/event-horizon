from event_horizon.carina.db import RewardCampaign, db_session


def delete_reward_campaign(campaign_slug: str) -> None:
    db_session.execute(RewardCampaign.__table__.delete().where(RewardCampaign.campaign_slug == campaign_slug))
    db_session.commit()
