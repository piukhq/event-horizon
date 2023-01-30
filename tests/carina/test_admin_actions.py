# pylint: disable=no-value-for-parameter,no-member

from typing import Any, NamedTuple
from unittest import mock

import httpretty

from pytest_mock import MockerFixture
from requests import RequestException
from sqlalchemy.orm import Session

from event_horizon.carina.admin import RewardAdmin, RewardConfigAdmin
from event_horizon.settings import CARINA_BASE_URL


class MockReward(NamedTuple):
    retailer_id: int
    allocated: bool
    deleted: bool


class MockRetailer(NamedTuple):
    slug: str


def test_delete_unallocated_rewards(mocker: MockerFixture) -> None:
    mock_flash = mocker.patch("event_horizon.carina.admin.flash")
    mock_send_activity = mocker.patch("event_horizon.carina.admin.sync_send_activity")

    def mock_init(self: Any, session: mock.MagicMock) -> None:
        self.session = session

    mocker.patch.object(RewardAdmin, "__init__", mock_init)
    mocker.patch.object(RewardAdmin, "sso_username", "test-user")

    # Mock 2 rewards for the same retailer, which are unallocated and not soft deleted
    mocker.patch("event_horizon.carina.admin.RewardAdmin._get_rewards_from_ids").return_value = [
        MockReward(retailer_id=1, allocated=False, deleted=False),
        MockReward(retailer_id=1, allocated=False, deleted=False),
    ]
    mocker.patch("event_horizon.carina.admin.RewardAdmin._get_retailer_by_id").return_value = MockRetailer(
        slug="test-retailer"
    )

    session = mock.MagicMock(
        rollback=mock.MagicMock(),
        delete=mock.MagicMock(),
        commit=mock.MagicMock(),
    )

    RewardAdmin(session).delete_rewards([1, 2])

    assert session.commit.call_count == 1  # Successfully call commit to delete the rewards
    assert session.rollback.call_count == 0
    mock_flash.assert_called_once_with("Successfully deleted selected rewards")

    mock_send_activity.assert_called_once()


def test_delete_unallocated_rewards_for_different_retailers(
    mocker: MockerFixture,
) -> None:
    mock_flash = mocker.patch("event_horizon.carina.admin.flash")
    mock_send_activity = mocker.patch("event_horizon.carina.admin.sync_send_activity")

    def mock_init(self: Any, session: mock.MagicMock) -> None:
        self.session = session

    mocker.patch.object(RewardAdmin, "__init__", mock_init)
    mocker.patch.object(RewardAdmin, "sso_username", "test-user")

    # Mock 2 rewards for different retailers, which are unallocated and not soft deleted
    mocker.patch("event_horizon.carina.admin.RewardAdmin._get_rewards_from_ids").return_value = [
        MockReward(retailer_id=1, allocated=False, deleted=False),
        MockReward(retailer_id=2, allocated=False, deleted=False),
    ]
    mocker.patch("event_horizon.carina.admin.RewardAdmin._get_retailer_by_id").return_value = MockRetailer(
        slug="test-retailer"
    )

    session = mock.MagicMock(
        rollback=mock.MagicMock(),
        delete=mock.MagicMock(),
        commit=mock.MagicMock(),
    )

    RewardAdmin(session).delete_rewards([1, 2])

    assert session.commit.call_count == 0  # Not commited any changes
    assert session.rollback.call_count == 1  # rollback due to failure
    mock_flash.assert_called_once_with("Not all selected rewards are for the same retailer", category="error")

    mock_send_activity.assert_not_called()  # Activity not sent


def test_delete_allocated_rewards(
    mocker: MockerFixture,
) -> None:
    mock_flash = mocker.patch("event_horizon.carina.admin.flash")
    mock_send_activity = mocker.patch("event_horizon.carina.admin.sync_send_activity")

    def mock_init(self: Any, session: mock.MagicMock) -> None:
        self.session = session

    mocker.patch.object(RewardAdmin, "__init__", mock_init)
    mocker.patch.object(RewardAdmin, "sso_username", "test-user")

    # Mock 2 rewards for same retailer, where atleast one is allocated and none are soft deleted
    mocker.patch("event_horizon.carina.admin.RewardAdmin._get_rewards_from_ids").return_value = [
        MockReward(retailer_id=1, allocated=False, deleted=False),
        MockReward(retailer_id=1, allocated=True, deleted=False),
    ]
    mocker.patch("event_horizon.carina.admin.RewardAdmin._get_retailer_by_id").return_value = MockRetailer(
        slug="test-retailer"
    )

    session = mock.MagicMock(
        rollback=mock.MagicMock(),
        delete=mock.MagicMock(),
        commit=mock.MagicMock(),
    )

    RewardAdmin(session).delete_rewards([1, 2])

    assert session.commit.call_count == 0  # Not commited any changes
    assert session.rollback.call_count == 1  # rollback due to failure
    mock_flash.assert_called_once_with("Not all selected rewards are eligible for deletion", category="error")

    mock_send_activity.assert_not_called()  # Activity not sent


@httpretty.activate
def test_deactivate_reward_type(mocker: MockerFixture) -> None:
    retailer_slug = "retailer_1"
    reward_slug = "10percentoff"
    url = f"{CARINA_BASE_URL}/{retailer_slug}/rewards/{reward_slug}"

    mock_session = mock.MagicMock(spec=Session)
    mocker.patch.object(
        RewardConfigAdmin,
        "_get_reward_config",
        return_value=mock.Mock(retailer=mock.Mock(slug=retailer_slug), reward_slug=reward_slug),
    )
    mocker.patch.object(RewardConfigAdmin, "__init__", return_value=None)
    mock_flash = mocker.patch("event_horizon.carina.admin.flash")

    httpretty.register_uri("DELETE", url, body={}, status=204)

    # Single reward configs only
    RewardConfigAdmin(mock_session).deactivate_reward_type(["1", "2"])
    mock_flash.assert_called_with(
        "This action must be completed for reward_configs one at a time",
        category="error",
    )

    # Successful request
    RewardConfigAdmin(mock_session).deactivate_reward_type(["1"])
    mock_flash.assert_called_with("Successfully diactivated reward_config")


@httpretty.activate
def test_error_deactivate_reward_type(mocker: MockerFixture) -> None:
    retailer_slug = "retailer_1"
    reward_slug = "10percentoff"
    url = f"{CARINA_BASE_URL}/{retailer_slug}/rewards/{reward_slug}"

    mock_session = mock.MagicMock(spec=Session)
    for exc_type in (ValueError, RequestException):
        mocker.patch.object(
            RewardConfigAdmin,
            "_get_reward_config",
            side_effect=exc_type("Something bad happened"),
        )
        mocker.patch.object(RewardConfigAdmin, "__init__", return_value=None)
        mock_flash = mocker.patch("event_horizon.carina.admin.flash")

        httpretty.register_uri("DELETE", url, body={}, status=500)

        # Error request
        RewardConfigAdmin(mock_session).deactivate_reward_type(["1"])
        mock_flash.assert_called_with("Something bad happened", category="error")
