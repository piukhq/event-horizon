# pylint: disable=no-value-for-parameter,no-member

from unittest import mock

import httpretty

from pytest_mock import MockerFixture
from requests import RequestException
from sqlalchemy.orm import Session

from event_horizon.carina.admin import RewardConfigAdmin
from event_horizon.settings import CARINA_BASE_URL


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
    mock_flash.assert_called_with("This action must be completed for reward_configs one at a time", category="error")

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
