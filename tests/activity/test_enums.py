import uuid

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from pytest_mock import MockFixture

from event_horizon.activity_utils.enums import ActivityType
from event_horizon.vela.enums import PendingRewardChoices


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
        "reasons": ["Created"],
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
    max_amount = 200

    new_values = {
        "threshold": threshold + 100,
        "increment": increment + 1,
        "increment_multiplier": increment_multiplier * 2,
        "max_amount": max_amount * 2,
    }
    original_values = {
        "threshold": threshold,
        "increment": increment,
        "increment_multiplier": increment_multiplier,
        "max_amount": max_amount,
    }

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
        "reasons": ["Updated"],
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
                    "max_amount": max_amount * 2,
                },
                "original_values": {
                    "increment": increment,
                    "increment_multiplier": increment_multiplier,
                    "threshold": threshold,
                    "max_amount": max_amount,
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
    max_amount = 200

    new_values = {
        "threshold": threshold + 100,
        "max_amount": max_amount * 2,
    }
    original_values = {"threshold": threshold, "max_amount": max_amount}

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
        "reasons": ["Updated"],
        "activity_identifier": campaign_slug,
        "user_id": user_name,
        "associated_value": "N/A",
        "retailer": retailer_slug,
        "campaigns": [campaign_slug],
        "data": {
            "earn_rule": {
                "new_values": {
                    "threshold": threshold + 100,
                    "max_amount": max_amount * 2,
                },
                "original_values": {
                    "threshold": threshold,
                    "max_amount": max_amount,
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
        "reasons": ["Updated"],
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
    max_amount = 200

    payload = ActivityType.get_earn_rule_deleted_activity_data(
        retailer_slug=retailer_slug,
        campaign_name=campaign_name,
        sso_username=user_name,
        activity_datetime=activity_datetime,
        campaign_slug=campaign_slug,
        threshold=threshold,
        increment=increment,
        increment_multiplier=increment_multiplier,
        max_amount=max_amount,
    )

    assert payload == {
        "type": ActivityType.EARN_RULE.name,
        "datetime": fake_now,
        "underlying_datetime": activity_datetime,
        "summary": f"{campaign_name} Earn Rule removed",
        "reasons": ["Deleted"],
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
                    "max_amount": max_amount,
                }
            }
        },
    }


def test_get_reward_rule_created_activity_data(mocker: MockFixture) -> None:
    mock_datetime = mocker.patch("event_horizon.activity_utils.enums.datetime")
    fake_now = datetime.now(tz=timezone.utc)
    mock_datetime.now.return_value = fake_now

    user_name = "TestUser"
    campaign_name = "Test Campaign"
    campaign_slug = "test-campaign"
    retailer_slug = "test-retailer"
    activity_datetime = datetime.now(tz=timezone.utc)
    reward_goal = 1000
    refund_window = 7
    reward_slug = "test-reward"

    payload = ActivityType.get_reward_rule_created_activity_data(
        retailer_slug=retailer_slug,
        campaign_name=campaign_name,
        sso_username=user_name,
        activity_datetime=activity_datetime,
        campaign_slug=campaign_slug,
        reward_goal=reward_goal,
        refund_window=refund_window,
        reward_slug=reward_slug,
    )

    assert payload == {
        "type": ActivityType.REWARD_RULE.name,
        "datetime": fake_now,
        "underlying_datetime": activity_datetime,
        "summary": f"{campaign_name} Reward Rule created",
        "reasons": ["Created"],
        "activity_identifier": campaign_slug,
        "user_id": user_name,
        "associated_value": "N/A",
        "retailer": retailer_slug,
        "campaigns": [campaign_slug],
        "data": {
            "reward_rule": {
                "new_values": {
                    "reward_goal": reward_goal,
                    "refund_window": refund_window,
                    "reward_slug": reward_slug,
                }
            }
        },
    }


def test_get_balance_change_activity_data(mocker: MockFixture) -> None:
    mock_datetime = mocker.patch("event_horizon.activity_utils.enums.datetime")
    fake_now = datetime.now(tz=timezone.utc)
    mock_datetime.now.return_value = fake_now

    account_holder_uuid = str(uuid.uuid4())
    from_campaign_slug = "ended-campaign"
    to_campaign_slug = "activated-campaign"
    retailer_slug = "test-retailer"
    activity_datetime = datetime.now(tz=timezone.utc)
    new_balance = 1200

    for loyalty_type in ["STAMPS", "ACCUMULATOR"]:

        if loyalty_type == "STAMPS":
            expected_associated_value = "12 stamps"
        else:
            expected_associated_value = "£12.00"

        payload = ActivityType.get_balance_change_activity_data(
            retailer_slug=retailer_slug,
            from_campaign_slug=from_campaign_slug,
            to_campaign_slug=to_campaign_slug,
            account_holder_uuid=account_holder_uuid,
            activity_datetime=activity_datetime,
            new_balance=new_balance,
            loyalty_type=loyalty_type,
        )

        assert payload == {
            "type": ActivityType.BALANCE_CHANGE.name,
            "datetime": fake_now,
            "underlying_datetime": activity_datetime,
            "summary": f"{retailer_slug} {to_campaign_slug} Balance {expected_associated_value}",
            "reasons": [f"Migrated from ended campaign {from_campaign_slug}"],
            "activity_identifier": "N/A",
            "user_id": account_holder_uuid,
            "associated_value": expected_associated_value,
            "retailer": retailer_slug,
            "campaigns": [to_campaign_slug],
            "data": {
                "loyalty_type": loyalty_type,
                "new_balance": new_balance,
                "original_balance": 0,
            },
        }


def test_get_campaign_migration_activity_data(mocker: MockFixture) -> None:
    mock_datetime = mocker.patch("event_horizon.activity_utils.enums.datetime")
    fake_now = datetime.now(tz=timezone.utc)
    mock_datetime.now.return_value = fake_now

    sso_username = "Test Runner"
    from_campaign_slug = "ended-campaign"
    to_campaign_slug = "activated-campaign"
    retailer_slug = "test-retailer"
    activity_datetime = datetime.now(tz=timezone.utc)
    balance_conversion_rate = 100
    qualify_threshold = 0
    pending_rewards = PendingRewardChoices.CONVERT

    payload = ActivityType.get_campaign_migration_activity_data(
        retailer_slug=retailer_slug,
        from_campaign_slug=from_campaign_slug,
        to_campaign_slug=to_campaign_slug,
        sso_username=sso_username,
        activity_datetime=activity_datetime,
        balance_conversion_rate=balance_conversion_rate,
        qualify_threshold=qualify_threshold,
        pending_rewards=pending_rewards,
    )

    assert payload == {
        "type": ActivityType.CAMPAIGN_MIGRATION.name,
        "datetime": fake_now,
        "underlying_datetime": activity_datetime,
        "summary": (
            f"{retailer_slug} Campaign {from_campaign_slug} has ended"
            f" and account holders have been migrated to Campaign {to_campaign_slug}"
        ),
        "reasons": [f"Campaign {from_campaign_slug} was ended"],
        "activity_identifier": retailer_slug,
        "user_id": sso_username,
        "associated_value": "N/A",
        "retailer": retailer_slug,
        "campaigns": [from_campaign_slug, to_campaign_slug],
        "data": {
            "ended_campaign": from_campaign_slug,
            "activated_campaign": to_campaign_slug,
            "balance_conversion_rate": f"{balance_conversion_rate}%",
            "qualify_threshold": f"{qualify_threshold}%",
            "pending_rewards": pending_rewards.value.lower(),
        },
    }
