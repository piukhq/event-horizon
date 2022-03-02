import json

from typing import Any
from unittest import mock

import httpretty

from pytest_mock import MockerFixture

from app.settings import VELA_BASE_URL
from app.vela.admin import CampaignAdmin


@httpretty.activate
def test__campaigns_status_change(mocker: MockerFixture) -> None:
    status = "active"
    retailer_slug = "retailer_1"
    url = f"{VELA_BASE_URL}/{retailer_slug}/campaigns/status_change"
    campaign_slug_1 = "campaign_1"
    campaign_slug_2 = "campaign_2"

    def mock_init(self: Any, session: mock.MagicMock) -> None:
        self.session = session

    mocker.patch.object(CampaignAdmin, "__init__", mock_init)
    mocker.patch("app.vela.admin.Campaign", slug=mock.Mock())
    mocker.patch("app.vela.admin.RetailerRewards", slug=mock.Mock())
    mocker.patch("app.vela.admin.select", slug=mock.Mock())
    mock_flash = mocker.patch("app.vela.admin.flash")

    httpretty.register_uri("POST", url, {}, status=202)
    session = mock.MagicMock(
        execute=lambda x: mock.MagicMock(
            all=lambda: [(campaign_slug_1, retailer_slug), (campaign_slug_2, "OTHER RETAILER")]
        )
    )
    CampaignAdmin(session)._campaigns_status_change(["1", "2"], status)

    assert httpretty.latest_requests() == []
    mock_flash.assert_called_once_with("All the selected campaigns must belong to the same retailer.", category="error")

    session = mock.MagicMock(
        execute=lambda x: mock.MagicMock(
            all=lambda: [(campaign_slug_1, retailer_slug), (campaign_slug_2, retailer_slug)]
        )
    )

    CampaignAdmin(session)._campaigns_status_change(["1", "2"], status)

    last_request = httpretty.last_request().parsed_body

    assert last_request["requested_status"] == status
    assert set(last_request["campaign_slugs"]) == {campaign_slug_1, campaign_slug_2}
    mock_flash.assert_called_with(f"Selected campaigns' status has been successfully changed to {status}")

    unexpected_error = {"what": "noooo"}
    httpretty.reset()
    httpretty.register_uri("POST", url, json.dumps(unexpected_error), status=500)
    CampaignAdmin(session)._campaigns_status_change(["1", "2"], status)

    mock_flash.assert_called_with(f"Unexpected response received: {unexpected_error}", category="error")

    list_error = [
        {
            "display_message": "Campaign not found for provided slug.",
            "code": "NO_CAMPAIGN_FOUND",
            "campaigns": [campaign_slug_1, campaign_slug_2],
        },
    ]
    httpretty.reset()
    httpretty.register_uri("POST", url, json.dumps(list_error), status=404)

    CampaignAdmin(session)._campaigns_status_change(["1", "2"], status)

    mock_flash.assert_called_with(
        f"{list_error[0]['display_message']} ::: {', '.join(list_error[0]['campaigns'])}",
        category="error",
    )

    dict_error = {
        "display_message": "Requested retailer is invalid.",
        "code": "INVALID_RETAILER",
    }
    httpretty.reset()
    httpretty.register_uri("POST", url, json.dumps(dict_error), status=403)

    CampaignAdmin(session)._campaigns_status_change(["1", "2"], status)

    mock_flash.assert_called_with(dict_error["display_message"], category="error")
