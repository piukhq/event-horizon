from event_horizon.vela.db import Campaign


def test_campaign_can_delete() -> None:
    for status in ("ACTIVE", "CANCELLED", "ENDED"):
        campaign = Campaign()
        campaign.status = status
        assert not campaign.can_delete

    campaign = Campaign()
    campaign.status = "DRAFT"
    assert campaign.can_delete
