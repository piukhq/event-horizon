import json
import uuid

from typing import Any
from unittest import mock

import httpretty

from pytest_mock import MockerFixture

from app.polaris.admin import AccountHolderAdmin
from app.settings import POLARIS_BASE_URL


@httpretty.activate
def test_anonymise_user(mocker: MockerFixture) -> None:
    retailer_slug = "retailer_1"
    account_holder_uuid = str(uuid.uuid4())
    url = f"{POLARIS_BASE_URL}/{retailer_slug}/accounts/{account_holder_uuid}/status"

    def mock_init(self: Any, session: mock.MagicMock) -> None:
        self.session = session

    session = mock.MagicMock(execute=lambda x: mock.MagicMock(first=lambda: (retailer_slug, account_holder_uuid)))
    mocker.patch.object(AccountHolderAdmin, "__init__", mock_init)
    mocker.patch("app.polaris.admin.RetailerConfig", slug=mock.Mock())
    mocker.patch("app.polaris.admin.AccountHolder", account_holder_uuid=mock.Mock())
    mocker.patch("app.polaris.admin.select", slug=mock.Mock())
    mock_flash = mocker.patch("app.polaris.admin.flash")
    mock_model_views_flash = mocker.patch("app.admin.model_views.flash")

    httpretty.register_uri("PATCH", url, {}, status=200)

    # Single account holders only
    AccountHolderAdmin(session).anonymise_user(["1", "2"])
    mock_flash.assert_called_once_with(
        "This action must be completed for account holders one at a time", category="error"
    )
    assert httpretty.latest_requests() == []

    AccountHolderAdmin(session).anonymise_user(["1"])
    last_request = httpretty.last_request().parsed_body
    assert last_request == {"status": "inactive"}
    mock_flash.assert_called_with("Account Holder successfully changed to INACTIVE")

    unexpected_error = {"what": "noooo"}
    httpretty.reset()
    httpretty.register_uri("PATCH", url, json.dumps(unexpected_error), status=500)
    AccountHolderAdmin(session).anonymise_user(["1"])
    assert last_request == {"status": "inactive"}
    mock_model_views_flash.assert_called_with(f"Unexpected response received: {unexpected_error}", category="error")
