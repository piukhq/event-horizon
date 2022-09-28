import copy

from uuid import uuid4

from pytest_mock import MockerFixture

from event_horizon.hubble.account_activity_rtbf import anonymise_account_activities
from event_horizon.hubble.enums import AccountActivities

ACCOUNT_REQUEST_MOCK_DATA = {
    "fields": [
        {"value": "foo", "field_name": "first_name"},
        {"value": "bar", "field_name": "last_name"},
        {"value": "Brakus.c5df93057c60@apple.com", "field_name": "email"},
        {"value": "LS21 081", "field_name": "postcode"},
        {"value": "[]", "field_name": "consents"},
        {"value": False, "field_name": "marketing_pref"},
    ],
    "channel": "com.barclays.bmb",
    "datetime": "2022-09-14T10:53:32.833499Z",
}


def test_anonymise_all_account_activities_request(mocker: MockerFixture) -> None:
    mock_activities = mocker.patch("event_horizon.hubble.account_activity_rtbf._get_all_account_activities")
    mock_logging = mocker.patch("event_horizon.hubble.account_activity_rtbf.logging.info")

    retailer_slug = "test-retailer"
    account_holder = mocker.MagicMock()
    account_holder.account_holder_uuid.return_value = str(uuid4())
    mock_email = "test@email.com"
    account_holder.email.return_value = mock_email

    params = {
        "id": str(uuid4()),
        "type": AccountActivities.ACCOUNT_REQUEST.value,
        "summary": f"Enrolment Requested for {mock_email}",
        "associated_value": mock_email,
        "data": copy.deepcopy(ACCOUNT_REQUEST_MOCK_DATA),
    }

    mock_activities.return_value = [
        [
            mocker.MagicMock(
                id=params["id"],
                type=params["type"],
                summary=params["summary"],
                associated_value=params["associated_value"],
                data=params["data"],
            )
        ]
    ]
    assert params["summary"] in mock_activities.return_value[0][0].summary
    assert params["associated_value"] in mock_activities.return_value[0][0].associated_value
    assert mock_activities.return_value[0][0].data == ACCOUNT_REQUEST_MOCK_DATA

    anonymise_account_activities(retailer_slug, account_holder.account_holder_uuid, account_holder.email)

    assert params["summary"] not in mock_activities.return_value[0][0].summary
    assert params["associated_value"] not in mock_activities.return_value[0][0].associated_value
    assert mock_activities.return_value[0][0].data != ACCOUNT_REQUEST_MOCK_DATA

    mock_logging.assert_called_once_with(
        "Successfully applied updates to the following activities: %s for account_holder_uuid: %s",
        [mock_activities.return_value[0][0].id],
        account_holder.account_holder_uuid,
    )
