import json
import uuid

from typing import Any
from unittest import mock

import httpretty

from pytest_mock import MockerFixture

from event_horizon.polaris.admin import AccountHolderAdmin, RetailerConfigAdmin
from event_horizon.settings import POLARIS_BASE_URL


@mock.patch("event_horizon.polaris.admin.anonymise_account_activities")
@httpretty.activate
def test_anonymise_user(mock_activity_call: mock.MagicMock, mocker: MockerFixture) -> None:
    retailer_slug = "retailer_1"
    account_holder_uuid = str(uuid.uuid4())
    account_holder = mock.MagicMock(account_holder_uuid=account_holder_uuid, email="test@email.com")
    url = f"{POLARIS_BASE_URL}/{retailer_slug}/accounts/{account_holder_uuid}/status"

    def mock_init(self: Any, session: mock.MagicMock) -> None:
        self.session = session

    session = mock.MagicMock(execute=lambda x: mock.MagicMock(first=lambda: (retailer_slug, account_holder)))
    mocker.patch.object(AccountHolderAdmin, "__init__", mock_init)
    mocker.patch("event_horizon.polaris.admin.RetailerConfig", slug=mock.Mock())
    mocker.patch("event_horizon.polaris.admin.AccountHolder", account_holder_uuid=mock.Mock())
    mocker.patch("event_horizon.polaris.admin.select", slug=mock.Mock())
    mock_flash = mocker.patch("event_horizon.polaris.admin.flash")
    mock_model_views_flash = mocker.patch("event_horizon.admin.model_views.flash")

    httpretty.register_uri("PATCH", url, {}, status=200)

    # Account holder is inactive
    account_holder.status = "INACTIVE"
    AccountHolderAdmin(session).anonymise_user(["1"])
    mock_flash.assert_called_with("Account holder is INACTIVE", category="error")
    assert not httpretty.latest_requests()

    # Single account holders only
    account_holder.status = "ACTIVE"
    AccountHolderAdmin(session).anonymise_user(["1", "2"])
    mock_flash.assert_called_with("This action must be completed for account holders one at a time", category="error")
    assert not httpretty.latest_requests()

    AccountHolderAdmin(session).anonymise_user(["1"])
    last_request = httpretty.last_request().parsed_body
    assert last_request == {"status": "inactive"}
    mock_flash.assert_called_with("Account Holder successfully changed to INACTIVE")

    # Annonymise account activity
    mock_activity_call.assert_called_once_with(
        retailer_slug=retailer_slug,
        account_holder_uuid=account_holder.account_holder_uuid,
        account_holder_email=account_holder.email,
    )

    unexpected_error = {"what": "noooo"}
    httpretty.reset()
    httpretty.register_uri("PATCH", url, json.dumps(unexpected_error), status=500)
    AccountHolderAdmin(session).anonymise_user(["1"])
    assert last_request == {"status": "inactive"}
    mock_model_views_flash.assert_called_with(f"Unexpected response received: {unexpected_error}", category="error")


def test_activate_retailer(mocker: MockerFixture) -> None:
    retailer = mock.MagicMock(status="TEST")

    def mock_init(self: Any, session: mock.MagicMock) -> None:
        self.session = session

    session = mock.MagicMock()
    mocker.patch.object(RetailerConfigAdmin, "__init__", mock_init)
    mocker.patch("event_horizon.polaris.admin.RetailerConfig", slug=mock.Mock())
    mocker.patch("event_horizon.polaris.admin.RetailerConfigAdmin._get_retailer_by_id").return_value = retailer
    mocker.patch("event_horizon.polaris.admin.check_activate_campaign_for_retailer").return_value = [1]
    mocker.patch("event_horizon.polaris.admin.sync_activate_retailer")
    mock_flash = mocker.patch("event_horizon.polaris.admin.flash")
    mocker.patch.object(RetailerConfigAdmin, "sso_username", "test-user")
    mock_send_activity = mocker.patch("event_horizon.polaris.admin.sync_send_activity")

    # More than one retailer ids in list
    RetailerConfigAdmin(session).activate_retailer(["1", "2"])
    mock_flash.assert_called_with("Cannot activate more than one retailer at once", category="error")
    assert mock_send_activity.call_count == 0

    # Successfully update retailer status
    assert retailer.status == "TEST"
    RetailerConfigAdmin(session).activate_retailer(["1"])
    mock_flash.assert_called_with("Update retailer status successfully")
    assert retailer.status == "ACTIVE"
    assert mock_send_activity.call_count == 1

    # Retailer not in test status
    assert retailer.status == "ACTIVE"
    RetailerConfigAdmin(session).activate_retailer(["1"])
    mock_flash.assert_called_with("Retailer in incorrect state for activation", category="error")
    assert retailer.status == "ACTIVE"

    # No active campaign for retailer
    retailer.status = "TEST"
    mocker.patch(
        "event_horizon.polaris.admin.check_activate_campaign_for_retailer"
    ).return_value = []  # no active campaigns
    RetailerConfigAdmin(session).activate_retailer(["1"])
    mock_flash.assert_called_with("Retailer has no active campaign", category="error")
    assert retailer.status == "TEST"

    assert mock_send_activity.call_count == 1
