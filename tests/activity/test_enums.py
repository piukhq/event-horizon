# pylint: disable=too-many-lines

import uuid

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import yaml

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
        "type": ActivityType.CAMPAIGN.name,
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
        "type": ActivityType.CAMPAIGN.name,
        "datetime": fake_now,
        "underlying_datetime": activity_datetime,
        "summary": f"{campaign_name} changed",
        "reasons": ["Updated"],
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
        "type": ActivityType.CAMPAIGN.name,
        "datetime": fake_now,
        "underlying_datetime": activity_datetime,
        "summary": f"{campaign_name} changed",
        "reasons": ["Updated"],
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


def test_get_campaign_deleted_activity_data_ok(mocker: MockFixture) -> None:
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

    payload = ActivityType.get_campaign_deleted_activity_data(
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
        "type": ActivityType.CAMPAIGN.name,
        "datetime": fake_now,
        "underlying_datetime": activity_datetime,
        "summary": f"{campaign_name} deleted",
        "reasons": ["Deleted"],
        "activity_identifier": campaign_slug,
        "user_id": user_name,
        "associated_value": "N/A",
        "retailer": retailer_slug,
        "campaigns": [campaign_slug],
        "data": {
            "campaign": {
                "original_values": {
                    "retailer": retailer_slug,
                    "name": campaign_name,
                    "slug": campaign_slug,
                    "loyalty_type": loyalty_type.title(),
                    "start_date": start_date.strftime("%Y-%m-%d %H:%M:%S"),
                    "end_date": end_date.strftime("%Y-%m-%d %H:%M:%S"),
                }
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

    for loyalty_type, max_amount, expected_new_values in (
        (
            "STAMPS",
            0,
            {
                "threshold": threshold,
                "increment": increment,
                "increment_multiplier": increment_multiplier,
            },
        ),
        (
            "STAMPS",
            10,
            {
                "threshold": threshold,
                "increment": increment,
                "increment_multiplier": increment_multiplier,
                "max_amount": 10,
            },
        ),
        (
            "ACCUMULATOR",
            0,
            {
                "threshold": threshold,
                "increment_multiplier": increment_multiplier,
            },
        ),
        (
            "ACCUMULATOR",
            10,
            {
                "threshold": threshold,
                "increment_multiplier": increment_multiplier,
                "max_amount": 10,
            },
        ),
    ):

        payload = ActivityType.get_earn_rule_created_activity_data(
            retailer_slug=retailer_slug,
            campaign_name=campaign_name,
            sso_username=user_name,
            activity_datetime=activity_datetime,
            campaign_slug=campaign_slug,
            loyalty_type=loyalty_type,  # type: ignore
            threshold=threshold,
            increment=increment,
            increment_multiplier=increment_multiplier,
            max_amount=max_amount,
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
                "loyalty_type": loyalty_type,
                "earn_rule": {
                    "new_values": expected_new_values,
                },
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
    reward_cap = 2

    payload = ActivityType.get_reward_rule_created_activity_data(
        retailer_slug=retailer_slug,
        campaign_name=campaign_name,
        sso_username=user_name,
        activity_datetime=activity_datetime,
        campaign_slug=campaign_slug,
        reward_goal=reward_goal,
        refund_window=refund_window,
        reward_slug=reward_slug,
        reward_cap=reward_cap,
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
                    "campaign_slug": campaign_slug,
                    "reward_goal": reward_goal,
                    "refund_window": refund_window,
                    "reward_slug": reward_slug,
                    "reward_cap": reward_cap,
                }
            }
        },
    }


def test_get_reward_rule_updated_activity_data(mocker: MockFixture) -> None:
    mock_datetime = mocker.patch("event_horizon.activity_utils.enums.datetime")
    fake_now = datetime.now(tz=timezone.utc)
    mock_datetime.now.return_value = fake_now

    user_name = "TestUser"
    original_campaign_name = "Test Campaign"
    original_campaign_slug = "test-campaign"
    retailer_slug = "test-retailer"
    activity_datetime = datetime.now(tz=timezone.utc)

    new_values = {
        "reward_goal": 500,
        "reward_slug": "new-slug",
        "campaign_slug": "new-campaign-slug",
        "allocation_window": 30,
        "reward_cap": 2,
    }
    original_values = {
        "reward_goal": 800,
        "reward_slug": "old-slug",
        "campaign_slug": original_campaign_slug,
        "allocation_window": 0,
        "reward_cap": 1,
    }

    payload = ActivityType.get_reward_rule_updated_activity_data(
        retailer_slug=retailer_slug,
        campaign_name=original_campaign_name,
        sso_username=user_name,
        activity_datetime=activity_datetime,
        campaign_slug=original_campaign_slug,
        new_values=new_values,
        original_values=original_values,
    )

    # The activity schema has an alias for allocation_window
    new_values["refund_window"] = new_values.pop("allocation_window")
    original_values["refund_window"] = original_values.pop("allocation_window")

    assert payload == {
        "type": ActivityType.REWARD_RULE.name,
        "datetime": fake_now,
        "underlying_datetime": activity_datetime,
        "summary": f"{original_campaign_name} Reward Rule changed",
        "reasons": ["Updated"],
        "activity_identifier": original_campaign_slug,
        "user_id": user_name,
        "associated_value": "N/A",
        "retailer": retailer_slug,
        "campaigns": [original_campaign_slug],
        "data": {
            "reward_rule": {
                "new_values": new_values,
                "original_values": original_values,
            }
        },
    }


def test_get_reward_rule_updated_activity_data_partial(mocker: MockFixture) -> None:
    mock_datetime = mocker.patch("event_horizon.activity_utils.enums.datetime")
    fake_now = datetime.now(tz=timezone.utc)
    mock_datetime.now.return_value = fake_now

    user_name = "TestUser"
    campaign_name = "Test Campaign"
    campaign_slug = "test-campaign"
    retailer_slug = "test-retailer"
    activity_datetime = datetime.now(tz=timezone.utc)

    new_values = {
        "reward_goal": 500,
        "reward_slug": "new-slug",
    }
    original_values = {
        "reward_goal": 800,
        "reward_slug": "old-slug",
    }

    payload = ActivityType.get_reward_rule_updated_activity_data(
        retailer_slug=retailer_slug,
        campaign_name=campaign_name,
        sso_username=user_name,
        activity_datetime=activity_datetime,
        campaign_slug=campaign_slug,
        new_values=new_values,
        original_values=original_values,
    )

    assert payload == {
        "type": ActivityType.REWARD_RULE.name,
        "datetime": fake_now,
        "underlying_datetime": activity_datetime,
        "summary": f"{campaign_name} Reward Rule changed",
        "reasons": ["Updated"],
        "activity_identifier": campaign_slug,
        "user_id": user_name,
        "associated_value": "N/A",
        "retailer": retailer_slug,
        "campaigns": [campaign_slug],
        "data": {
            "reward_rule": {
                "new_values": new_values,
                "original_values": original_values,
            }
        },
    }


def test_get_reward_rule_deleted_activity_data(mocker: MockFixture) -> None:
    mock_datetime = mocker.patch("event_horizon.activity_utils.enums.datetime")
    fake_now = datetime.now(tz=timezone.utc)
    mock_datetime.now.return_value = fake_now

    user_name = "TestUser"
    campaign_name = "Test Campaign"
    campaign_slug = "test-campaign"
    retailer_slug = "test-retailer"
    activity_datetime = datetime.now(tz=timezone.utc)

    reward_goal = 800
    reward_slug = "old-slug"
    allocation_window = 0
    reward_cap = 1

    payload = ActivityType.get_reward_rule_deleted_activity_data(
        retailer_slug=retailer_slug,
        campaign_name=campaign_name,
        sso_username=user_name,
        activity_datetime=activity_datetime,
        campaign_slug=campaign_slug,
        reward_slug=reward_slug,
        reward_goal=reward_goal,
        refund_window=allocation_window,
        reward_cap=reward_cap,
    )

    assert payload == {
        "type": ActivityType.REWARD_RULE.name,
        "datetime": fake_now,
        "underlying_datetime": activity_datetime,
        "summary": f"{campaign_name} Reward Rule deleted",
        "reasons": ["Deleted"],
        "activity_identifier": campaign_slug,
        "user_id": user_name,
        "associated_value": "N/A",
        "retailer": retailer_slug,
        "campaigns": [campaign_slug],
        "data": {
            "reward_rule": {
                "original_values": {
                    "campaign_slug": campaign_slug,
                    "reward_goal": reward_goal,
                    "reward_slug": reward_slug,
                    "refund_window": allocation_window,
                    "reward_cap": reward_cap,
                },
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

    for loyalty_type in ("STAMPS", "ACCUMULATOR"):

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
        assert uuid.UUID(payload.pop("id")), "payload.id is not a uuid"
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

    payload_transfer_balance_requested = ActivityType.get_campaign_migration_activity_data(
        transfer_balance_requested=True,
        retailer_slug=retailer_slug,
        from_campaign_slug=from_campaign_slug,
        to_campaign_slug=to_campaign_slug,
        sso_username=sso_username,
        activity_datetime=activity_datetime,
        balance_conversion_rate=balance_conversion_rate,
        qualify_threshold=qualify_threshold,
        pending_rewards=pending_rewards,
    )

    assert payload_transfer_balance_requested == {
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

    payload_transfer_balance_not_requested = ActivityType.get_campaign_migration_activity_data(
        transfer_balance_requested=False,
        retailer_slug=retailer_slug,
        from_campaign_slug=from_campaign_slug,
        to_campaign_slug=to_campaign_slug,
        sso_username=sso_username,
        activity_datetime=activity_datetime,
        balance_conversion_rate=balance_conversion_rate,
        qualify_threshold=qualify_threshold,
        pending_rewards=pending_rewards,
    )

    assert payload_transfer_balance_not_requested == {
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
            "pending_rewards": pending_rewards.value.lower(),
        },
    }


def test_get_retailer_config_created_activity_data(mocker: MockFixture) -> None:
    mock_datetime = mocker.patch("event_horizon.activity_utils.enums.datetime")
    fake_now = datetime.now(tz=timezone.utc)
    mock_datetime.now.return_value = fake_now

    user_name = "TestUser"
    retailer_slug = "test-retailer"
    retailer_name = "Test retailer"
    activity_datetime = datetime.now(tz=timezone.utc)
    account_prefix = "RETB"
    loyalty_name = "mock retailer"
    retailer_status = "TEST"
    balance_lifespan = 30
    balance_reset_advanced_warning_days = 10

    retailer_enrol_config = """
email:
    required: true
    label: email
first_name:
    required: true
    label: First name
last_name:
    required: true
    label: Last name
"""

    marketing_pref_config = """
marketing_pref:
    label: Would you like emails?
    type: boolean
"""

    payload = ActivityType.get_retailer_created_activity_data(
        sso_username=user_name,
        activity_datetime=activity_datetime,
        status=retailer_status,
        retailer_name=retailer_name,
        retailer_slug=retailer_slug,
        account_number_prefix=account_prefix,
        enrolment_config=yaml.safe_load(retailer_enrol_config),
        marketing_preferences=yaml.safe_load(marketing_pref_config),
        loyalty_name=loyalty_name,
        balance_lifespan=balance_lifespan,
        balance_reset_advanced_warning_days=balance_reset_advanced_warning_days,
    )

    assert payload == {
        "type": ActivityType.RETAILER.name,
        "datetime": fake_now,
        "underlying_datetime": activity_datetime,
        "summary": f"{retailer_name} retailer created",
        "reasons": ["Created"],
        "activity_identifier": retailer_slug,
        "user_id": user_name,
        "associated_value": "N/A",
        "retailer": retailer_slug,
        "campaigns": [],
        "data": {
            "retailer": {
                "new_values": {
                    "status": retailer_status,
                    "name": retailer_name,
                    "slug": retailer_slug,
                    "account_number_prefix": account_prefix,
                    "enrolment_config": [
                        {"key": "email", "required": True, "label": "email"},
                        {"key": "first_name", "required": True, "label": "First name"},
                        {"key": "last_name", "required": True, "label": "Last name"},
                    ],
                    "marketing_preference_config": [
                        {"key": "marketing_pref", "type": "boolean", "label": "Would you like emails?"}
                    ],
                    "loyalty_name": loyalty_name,
                }
            },
        },
    }


def test_get_retailer_config_created_activity_data_without_optionals(mocker: MockFixture) -> None:
    mock_datetime = mocker.patch("event_horizon.activity_utils.enums.datetime")
    fake_now = datetime.now(tz=timezone.utc)
    mock_datetime.now.return_value = fake_now

    user_name = "TestUser"
    retailer_slug = "test-retailer"
    retailer_name = "Test retailer"
    activity_datetime = datetime.now(tz=timezone.utc)
    account_prefix = "RETB"
    loyalty_name = "mock retailer"
    retailer_status = "TEST"
    balance_lifespan = 0
    balance_reset_advanced_warning_days = 0

    retailer_enrol_config = """
email:
    required: true
first_name:
    required: true
last_name:
    required: true
    label: Last name
"""

    payload = ActivityType.get_retailer_created_activity_data(
        sso_username=user_name,
        activity_datetime=activity_datetime,
        status=retailer_status,
        retailer_name=retailer_name,
        retailer_slug=retailer_slug,
        account_number_prefix=account_prefix,
        enrolment_config=yaml.safe_load(retailer_enrol_config),
        marketing_preferences=yaml.safe_load(""),
        loyalty_name=loyalty_name,
        balance_lifespan=balance_lifespan,
        balance_reset_advanced_warning_days=balance_reset_advanced_warning_days,
    )

    assert payload == {
        "type": ActivityType.RETAILER.name,
        "datetime": fake_now,
        "underlying_datetime": activity_datetime,
        "summary": f"{retailer_name} retailer created",
        "reasons": ["Created"],
        "activity_identifier": retailer_slug,
        "user_id": user_name,
        "associated_value": "N/A",
        "retailer": retailer_slug,
        "campaigns": [],
        "data": {
            "retailer": {
                "new_values": {
                    "status": retailer_status,
                    "name": retailer_name,
                    "slug": retailer_slug,
                    "account_number_prefix": account_prefix,
                    "enrolment_config": [
                        {"key": "email", "required": True},
                        {"key": "first_name", "required": True},
                        {"key": "last_name", "required": True, "label": "Last name"},
                    ],
                    "loyalty_name": loyalty_name,
                }
            },
        },
    }


def test_get_reward_status_activity_data(mocker: MockFixture) -> None:
    mock_datetime = mocker.patch("event_horizon.activity_utils.enums.datetime")
    fake_now = datetime.now(tz=timezone.utc)
    mock_datetime.now.return_value = fake_now

    account_holder_uuid = str(uuid.uuid4())
    from_campaign_slug = "ended-campaign"
    to_campaign_slug = "activated-campaign"
    retailer_slug = "test-retailer"
    activity_datetime = datetime.now(tz=timezone.utc)
    pending_reward_uuid = str(uuid.uuid4())

    payload = ActivityType.get_reward_status_activity_data(
        retailer_slug=retailer_slug,
        from_campaign_slug=from_campaign_slug,
        to_campaign_slug=to_campaign_slug,
        account_holder_uuid=account_holder_uuid,
        activity_datetime=activity_datetime,
        pending_reward_uuid=pending_reward_uuid,
    )

    assert uuid.UUID(payload.pop("id")), "payload.id is not a uuid"
    assert payload == {
        "type": ActivityType.REWARD_STATUS.name,
        "datetime": fake_now,
        "underlying_datetime": activity_datetime,
        "summary": f"{retailer_slug} pending reward transferred from {from_campaign_slug} to {to_campaign_slug}",
        "reasons": ["Pending reward transferred at campaign end"],
        "activity_identifier": pending_reward_uuid,
        "user_id": account_holder_uuid,
        "associated_value": "N/A",
        "retailer": retailer_slug,
        "campaigns": [from_campaign_slug, to_campaign_slug],
        "data": {
            "old_campaign": from_campaign_slug,
            "new_campaign": to_campaign_slug,
        },
    }


def test_delete_account_holder_activity_data(mocker: MockFixture) -> None:
    mock_datetime = mocker.patch("event_horizon.activity_utils.enums.datetime")
    fake_now = datetime.now(tz=timezone.utc)
    mock_datetime.now.return_value = fake_now

    activity_datetime = datetime.now(tz=timezone.utc)
    account_holder_uuid = str(uuid.uuid4())

    payload = ActivityType.get_account_holder_deleted_activity_data(
        activity_datetime=activity_datetime,
        account_holder_uuid=account_holder_uuid,
        retailer_name="test retailer",
        retailer_status="TEST",
        retailer_slug="test-retailer",
        sso_username="Jane Doe",
    )

    assert uuid.UUID(payload.pop("id")), "payload.id is not a uuid"
    assert payload == {
        "type": ActivityType.ACCOUNT_DELETED.name,
        "datetime": fake_now,
        "underlying_datetime": activity_datetime,
        "summary": "Account holder deleted for test retailer",
        "reasons": ["Deleted"],
        "activity_identifier": account_holder_uuid,
        "user_id": "Jane Doe",
        "associated_value": "TEST",
        "retailer": "test-retailer",
        "campaigns": [],
        "data": {},
    }


def test_get_retailer_status_update_activity_data(mocker: MockFixture) -> None:
    mock_datetime = mocker.patch("event_horizon.activity_utils.enums.datetime")
    fake_now = datetime.now(tz=timezone.utc)
    mock_datetime.now.return_value = fake_now

    user_name = "TestUser"
    retailer_slug = "test-retailer"
    retailer_name = "Test retailer"
    activity_datetime = datetime.now(tz=timezone.utc)
    original_status = "TEST"
    new_status = "ACTIVE"

    payload = ActivityType.get_retailer_status_update_activity_data(
        sso_username=user_name,
        activity_datetime=activity_datetime,
        new_status=new_status,
        original_status=original_status,
        retailer_name=retailer_name,
        retailer_slug=retailer_slug,
    )

    assert payload == {
        "type": ActivityType.RETAILER_STATUS.name,
        "datetime": fake_now,
        "underlying_datetime": activity_datetime,
        "summary": f"{retailer_name} status is {new_status}",
        "reasons": ["Updated"],
        "activity_identifier": retailer_slug,
        "user_id": user_name,
        "associated_value": new_status,
        "retailer": retailer_slug,
        "campaigns": [],
        "data": {
            "retailer": {
                "new_values": {
                    "status": new_status,
                },
                "original_values": {
                    "status": original_status,
                },
            },
        },
    }
