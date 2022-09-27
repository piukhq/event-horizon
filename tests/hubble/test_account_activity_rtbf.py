import copy

from uuid import uuid4

from pytest_mock import MockerFixture

from event_horizon.hubble.account_activity_rtbf import (
    _anonymise_account_request_activity,
    _anonymise_generic_account_activity,
    anonymise_account_activities,
)
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


def test_anonymise_account_request_activity(mocker: MockerFixture) -> None:
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

    mock_activity = mocker.MagicMock(
        id=params["id"],
        type=params["type"],
        summary=params["summary"],
        associated_value=params["associated_value"],
        data=params["data"],
    )

    assert params["summary"] in mock_activity.summary
    assert params["associated_value"] in mock_activity.associated_value
    assert mock_activity.data == ACCOUNT_REQUEST_MOCK_DATA

    _anonymise_account_request_activity(mock_activity, account_holder.account_holder_uuid)

    assert params["summary"] not in mock_activity.summary
    assert params["associated_value"] not in mock_activity.associated_value
    assert mock_activity.data != ACCOUNT_REQUEST_MOCK_DATA


def test_anonymise_generic_account_activity(mocker: MockerFixture) -> None:
    account_holder_uuid = str(uuid4())

    params = {"id": str(uuid4()), "user_id": str(uuid4())}
    for activity in AccountActivities:
        if activity == AccountActivities.ACCOUNT_REQUEST:
            continue
        params["type"] = activity.value
        mock_activity = mocker.MagicMock(id=params["id"], type=params["type"], user_id=params["user_id"])

        assert mock_activity.user_id == params["user_id"]

        _anonymise_generic_account_activity(mock_activity, account_holder_uuid)

        assert params["user_id"] not in mock_activity.user_id
