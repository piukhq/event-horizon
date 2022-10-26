from datetime import datetime, timedelta, timezone
from decimal import Decimal

from pytest_mock import MockFixture

from event_horizon.activity_utils.enums import ActivityType


def test_get_campaign_created_activity_data(mocker: MockFixture) -> None:
    mock_datetime = mocker.patch("event_horizon.activity_utils.enums.datetime")
    fake_now = datetime.now(tz=timezone.utc)
    mock_datetime.now.return_value = fake_now

    user_name = "TestUser"
    campaign_name = "Test Campaign"
    campaign_slug = "test-campaign"
    loyalty_type = "ACCUMULATOR"
    retailer_slug = "test-retailer"
    activity_datetime = datetime.now(tz=timezone.utc)
    start_date = datetime.now(tz=timezone.utc)
    end_date = start_date + timedelta(days=30)

    payload = ActivityType.get_campaign_created_activity_data(
        retailer_slug=retailer_slug,
        campaign_name=campaign_name,
        sso_username=user_name,
        activity_datetime=activity_datetime,
        campaign_slug=campaign_slug,
        loyalty_type=loyalty_type,
        start_date=start_date,
        end_date=end_date,
    )

    assert payload == {
        "type": ActivityType.CAMPAIGN_CHANGE.name,
        "datetime": fake_now,
        "underlying_datetime": activity_datetime,
        "summary": f"{campaign_name} created",
        "reasons": [],
        "activity_identifier": campaign_slug,
        "user_id": user_name,
        "associated_value": "N/A",
        "retailer": retailer_slug,
        "campaigns": [campaign_slug],
        "data": {
            "campaign": {
                "new_values": {
                    "name": campaign_name,
                    "slug": campaign_slug,
                    "status": "draft",
                    "loyalty_type": loyalty_type.title(),
                    "start_date": start_date.strftime("%Y-%m-%d %H:%M:%S"),
                    "end_date": end_date.strftime("%Y-%m-%d %H:%M:%S"),
                }
            }
        },
    }


def test_get_campaign_updated_activity_data_ok(mocker: MockFixture) -> None:
    mock_datetime = mocker.patch("event_horizon.activity_utils.enums.datetime")
    fake_now = datetime.now(tz=timezone.utc)
    mock_datetime.now.return_value = fake_now

    user_name = "TestUser"
    campaign_name = "Test Campaign"
    campaign_slug = "test-campaign"
    retailer_slug = "test-retailer"
    activity_datetime = datetime.now(tz=timezone.utc)

    new_values = {"slug": "new-slug"}
    original_values = {"slug": "old-slug"}

    payload = ActivityType.get_campaign_updated_activity_data(
        retailer_slug=retailer_slug,
        campaign_name=campaign_name,
        sso_username=user_name,
        activity_datetime=activity_datetime,
        campaign_slug=campaign_slug,
        new_values=new_values,
        original_values=original_values,
    )

    assert payload == {
        "type": ActivityType.CAMPAIGN_CHANGE.name,
        "datetime": fake_now,
        "underlying_datetime": activity_datetime,
        "summary": f"{campaign_name} changed",
        "reasons": [],
        "activity_identifier": campaign_slug,
        "user_id": user_name,
        "associated_value": "N/A",
        "retailer": retailer_slug,
        "campaigns": [campaign_slug],
        "data": {
            "campaign": {
                "new_values": new_values,
                "original_values": original_values,
            }
        },
    }


def test_get_campaign_updated_activity_data_ignored_field(mocker: MockFixture) -> None:
    mock_datetime = mocker.patch("event_horizon.activity_utils.enums.datetime")
    fake_now = datetime.now(tz=timezone.utc)
    mock_datetime.now.return_value = fake_now

    user_name = "TestUser"
    campaign_name = "Test Campaign"
    campaign_slug = "test-campaign"
    retailer_slug = "test-retailer"
    activity_datetime = datetime.now(tz=timezone.utc)

    new_values = {"retailerrewards": "new-slug"}
    original_values = {"retailerrewards": "old-slug"}

    payload = ActivityType.get_campaign_updated_activity_data(
        retailer_slug=retailer_slug,
        campaign_name=campaign_name,
        sso_username=user_name,
        activity_datetime=activity_datetime,
        campaign_slug=campaign_slug,
        new_values=new_values,
        original_values=original_values,
    )

    assert payload == {
        "type": ActivityType.CAMPAIGN_CHANGE.name,
        "datetime": fake_now,
        "underlying_datetime": activity_datetime,
        "summary": f"{campaign_name} changed",
        "reasons": [],
        "activity_identifier": campaign_slug,
        "user_id": user_name,
        "associated_value": "N/A",
        "retailer": retailer_slug,
        "campaigns": [campaign_slug],
        "data": {
            "campaign": {
                "new_values": {},
                "original_values": {},
            }
        },
    }


def test_get_earn_rule_created_activity_data(mocker: MockFixture) -> None:
    mock_datetime = mocker.patch("event_horizon.activity_utils.enums.datetime")
    fake_now = datetime.now(tz=timezone.utc)
    mock_datetime.now.return_value = fake_now

    user_name = "TestUser"
    campaign_name = "Test Campaign"
    campaign_slug = "test-campaign"
    retailer_slug = "test-retailer"
    activity_datetime = datetime.now(tz=timezone.utc)
    threshold = 500
    increment = 1
    increment_multiplier = Decimal(2)

    payload = ActivityType.get_earn_rule_created_activity_data(
        retailer_slug=retailer_slug,
        campaign_name=campaign_name,
        sso_username=user_name,
        activity_datetime=activity_datetime,
        campaign_slug=campaign_slug,
        threshold=threshold,
        increment=increment,
        increment_multiplier=increment_multiplier,
    )

    assert payload == {
        "type": ActivityType.EARN_RULE.name,
        "datetime": fake_now,
        "underlying_datetime": activity_datetime,
        "summary": f"{campaign_name} Earn Rule created",
        "reasons": [],
        "activity_identifier": campaign_slug,
        "user_id": user_name,
        "associated_value": "N/A",
        "retailer": retailer_slug,
        "campaigns": [campaign_slug],
        "data": {
            "earn_rule": {
                "new_values": {
                    "threshold": threshold,
                    "increment": increment,
                    "increment_multiplier": increment_multiplier,
                }
            }
        },
    }


def test_get_earn_rule_updated_activity_data(mocker: MockFixture) -> None:
    mock_datetime = mocker.patch("event_horizon.activity_utils.enums.datetime")
    fake_now = datetime.now(tz=timezone.utc)
    mock_datetime.now.return_value = fake_now

    user_name = "TestUser"
    campaign_name = "Test Campaign"
    campaign_slug = "test-campaign"
    retailer_slug = "test-retailer"
    activity_datetime = datetime.now(tz=timezone.utc)
    threshold = 500
    increment = 1
    increment_multiplier = Decimal(2)

    new_values = {
        "threshold": threshold + 100,
        "increment": increment + 1,
        "increment_multiplier": increment_multiplier * 2,
    }
    original_values = {"threshold": threshold, "increment": increment, "increment_multiplier": increment_multiplier}

    payload = ActivityType.get_earn_rule_updated_activity_data(
        retailer_slug=retailer_slug,
        campaign_name=campaign_name,
        sso_username=user_name,
        activity_datetime=activity_datetime,
        campaign_slug=campaign_slug,
        new_values=new_values,
        original_values=original_values,
    )

    assert payload == {
        "type": ActivityType.EARN_RULE.name,
        "datetime": fake_now,
        "underlying_datetime": activity_datetime,
        "summary": f"{campaign_name} Earn Rule changed",
        "reasons": [],
        "activity_identifier": campaign_slug,
        "user_id": user_name,
        "associated_value": "N/A",
        "retailer": retailer_slug,
        "campaigns": [campaign_slug],
        "data": {
            "earn_rule": {
                "new_values": {
                    "threshold": threshold + 100,
                    "increment": increment + 1,
                    "increment_multiplier": increment_multiplier * 2,
                },
                "original_values": {
                    "increment": increment,
                    "increment_multiplier": increment_multiplier,
                    "threshold": threshold,
                },
            }
        },
    }


def test_get_earn_rule_updated_activity_partial_data(mocker: MockFixture) -> None:
    mock_datetime = mocker.patch("event_horizon.activity_utils.enums.datetime")
    fake_now = datetime.now(tz=timezone.utc)
    mock_datetime.now.return_value = fake_now

    user_name = "TestUser"
    campaign_name = "Test Campaign"
    campaign_slug = "test-campaign"
    retailer_slug = "test-retailer"
    activity_datetime = datetime.now(tz=timezone.utc)
    threshold = 500

    new_values = {
        "threshold": threshold + 100,
    }
    original_values = {"threshold": threshold}

    payload = ActivityType.get_earn_rule_updated_activity_data(
        retailer_slug=retailer_slug,
        campaign_name=campaign_name,
        sso_username=user_name,
        activity_datetime=activity_datetime,
        campaign_slug=campaign_slug,
        new_values=new_values,
        original_values=original_values,
    )

    assert payload == {
        "type": ActivityType.EARN_RULE.name,
        "datetime": fake_now,
        "underlying_datetime": activity_datetime,
        "summary": f"{campaign_name} Earn Rule changed",
        "reasons": [],
        "activity_identifier": campaign_slug,
        "user_id": user_name,
        "associated_value": "N/A",
        "retailer": retailer_slug,
        "campaigns": [campaign_slug],
        "data": {
            "earn_rule": {
                "new_values": {
                    "threshold": threshold + 100,
                },
                "original_values": {
                    "threshold": threshold,
                },
            }
        },
    }


def test_get_earn_rule_updated_activity_data_ignored_field(mocker: MockFixture) -> None:
    mock_datetime = mocker.patch("event_horizon.activity_utils.enums.datetime")
    fake_now = datetime.now(tz=timezone.utc)
    mock_datetime.now.return_value = fake_now

    user_name = "TestUser"
    campaign_name = "Test Campaign"
    campaign_slug = "test-campaign"
    retailer_slug = "test-retailer"
    activity_datetime = datetime.now(tz=timezone.utc)

    new_values = {"retailerrewards": "new-slug"}
    original_values = {"retailerrewards": "old-slug"}

    payload = ActivityType.get_earn_rule_updated_activity_data(
        retailer_slug=retailer_slug,
        campaign_name=campaign_name,
        sso_username=user_name,
        activity_datetime=activity_datetime,
        campaign_slug=campaign_slug,
        new_values=new_values,
        original_values=original_values,
    )

    assert payload == {
        "type": ActivityType.EARN_RULE.name,
        "datetime": fake_now,
        "underlying_datetime": activity_datetime,
        "summary": f"{campaign_name} Earn Rule changed",
        "reasons": [],
        "activity_identifier": campaign_slug,
        "user_id": user_name,
        "associated_value": "N/A",
        "retailer": retailer_slug,
        "campaigns": [campaign_slug],
        "data": {
            "earn_rule": {
                "new_values": {},
                "original_values": {},
            }
        },
    }


def test_get_earn_rule_deleted_activity_data(mocker: MockFixture) -> None:
    mock_datetime = mocker.patch("event_horizon.activity_utils.enums.datetime")
    fake_now = datetime.now(tz=timezone.utc)
    mock_datetime.now.return_value = fake_now

    user_name = "TestUser"
    campaign_name = "Test Campaign"
    campaign_slug = "test-campaign"
    retailer_slug = "test-retailer"
    activity_datetime = datetime.now(tz=timezone.utc)
    threshold = 500
    increment = 1
    increment_multiplier = Decimal(2)

    payload = ActivityType.get_earn_rule_deleted_activity_data(
        retailer_slug=retailer_slug,
        campaign_name=campaign_name,
        sso_username=user_name,
        activity_datetime=activity_datetime,
        campaign_slug=campaign_slug,
        threshold=threshold,
        increment=increment,
        increment_multiplier=increment_multiplier,
    )

    assert payload == {
        "type": ActivityType.EARN_RULE.name,
        "datetime": fake_now,
        "underlying_datetime": activity_datetime,
        "summary": f"{campaign_name} Earn Rule removed",
        "reasons": [],
        "activity_identifier": campaign_slug,
        "user_id": user_name,
        "associated_value": "N/A",
        "retailer": retailer_slug,
        "campaigns": [campaign_slug],
        "data": {
            "earn_rule": {
                "original_values": {
                    "threshold": threshold,
                    "increment": increment,
                    "increment_multiplier": increment_multiplier,
                }
            }
        },
    }
