import base64
import pickle

from collections.abc import Generator
from typing import NamedTuple
from unittest.mock import MagicMock

import pytest

from flask import Flask
from pytest_mock import MockerFixture
from sqlalchemy.exc import DataError

from event_horizon.polaris.custom_actions import DeleteRetailerAction, SessionData


class MockedRetailerConfig(NamedTuple):
    id: int
    slug: str
    name: str
    status: str


class SessionTestData(NamedTuple):
    value: SessionData
    b64str: str


class DeleteActionMockedDBCalls(NamedTuple):
    get_retailer_by_id: MagicMock
    delete_polaris_retailer_data: MagicMock
    delete_vela_retailer_data: MagicMock
    delete_carina_retailer_data: MagicMock
    delete_hubble_retailer_data: MagicMock


class DBSessionsMocks(NamedTuple):
    polaris_db_session: MagicMock
    vela_db_session: MagicMock
    carina_db_session: MagicMock
    hubble_db_session: MagicMock


@pytest.fixture(name="test_session_data")
def test_session_data_fixture() -> SessionTestData:
    session_data = SessionData(
        retailer_slug="test-retailer",
        retailer_name="Test Retailer",
        polaris_retailer_id=1,
        retailer_status="TEST",
        loyalty_name="ACCUMULATOR",
    )

    return SessionTestData(
        value=session_data,
        b64str=base64.b64encode(pickle.dumps(session_data)).decode(),
    )


@pytest.fixture(name="delete_action")
def delete_action_fixture() -> Generator[DeleteRetailerAction, None, None]:
    app = Flask(__name__)
    app.secret_key = "random string"
    with app.app_context(), app.test_request_context():
        yield DeleteRetailerAction()


@pytest.fixture(name="delete_action_mocks")
def delete_action_mocks_fixture(
    mocker: MockerFixture, delete_action: DeleteRetailerAction
) -> DeleteActionMockedDBCalls:
    return DeleteActionMockedDBCalls(
        get_retailer_by_id=mocker.patch.object(
            delete_action,
            "_get_retailer_by_id",
            return_value=MockedRetailerConfig(
                id=1,
                slug="test-retailer",
                name="Test Retailer",
                status="TEST",
            ),
        ),
        delete_polaris_retailer_data=mocker.patch.object(delete_action, "_delete_polaris_retailer_data"),
        delete_vela_retailer_data=mocker.patch.object(delete_action, "_delete_vela_retailer_data"),
        delete_carina_retailer_data=mocker.patch.object(delete_action, "_delete_carina_retailer_data"),
        delete_hubble_retailer_data=mocker.patch.object(delete_action, "_delete_hubble_retailer_data"),
    )


@pytest.fixture(name="db_sessions_mocks")
def db_sessions_mocks_fixture(mocker: MockerFixture) -> DBSessionsMocks:
    return DBSessionsMocks(
        polaris_db_session=mocker.patch("event_horizon.polaris.custom_actions.polaris_db_session"),
        vela_db_session=mocker.patch("event_horizon.polaris.custom_actions.vela_db_session"),
        carina_db_session=mocker.patch("event_horizon.polaris.custom_actions.carina_db_session"),
        hubble_db_session=mocker.patch("event_horizon.polaris.custom_actions.hubble_db_session"),
    )


def test_session_data_methods(test_session_data: SessionTestData) -> None:
    assert test_session_data.value.to_base64_str() == test_session_data.b64str
    assert SessionData.from_base64_str(test_session_data.b64str) == test_session_data.value


def test_delete_retailer_action_session_form_data(
    delete_action: DeleteRetailerAction, test_session_data: SessionTestData
) -> None:
    with pytest.raises(ValueError) as ex_info:
        delete_action.session_data

    assert ex_info.value.args[0] == "session_data is not set"

    delete_action.session_data = test_session_data.b64str  # type: ignore [assignment]
    assert delete_action.session_data == test_session_data.value


def test_validate_selected_ids_no_ids(delete_action: DeleteRetailerAction) -> None:
    assert delete_action.validate_selected_ids([]) == "no retailer selected."


def test_validate_selected_ids_too_many_ids(delete_action: DeleteRetailerAction) -> None:
    assert delete_action.validate_selected_ids(["1", "2"]) == "Only one Retailer allowed for this action"


def test_validate_selected_ids_wrong_status(
    delete_action: DeleteRetailerAction, delete_action_mocks: DeleteActionMockedDBCalls
) -> None:
    delete_action_mocks.get_retailer_by_id.return_value = MockedRetailerConfig(
        id=1, slug="test-retailer", name="Test Retailer", status="ACTIVE"
    )
    assert delete_action.validate_selected_ids(["1"]) == "Only non active Retailers allowed for this action"
    delete_action_mocks.get_retailer_by_id.assert_called_once_with(1)


def test_delete_retailer_ok_user_agreed(
    mocker: MockerFixture,
    delete_action: DeleteRetailerAction,
    test_session_data: SessionTestData,
    db_sessions_mocks: DBSessionsMocks,
    delete_action_mocks: DeleteActionMockedDBCalls,
) -> None:
    assert delete_action.validate_selected_ids(["1"]) is None
    assert delete_action.session_data == test_session_data.value
    delete_action_mocks.get_retailer_by_id.assert_called_once_with(1)

    mocked_flash = mocker.patch("event_horizon.polaris.custom_actions.flash")
    mocked_logger = mocker.patch.object(delete_action, "logger")
    delete_action.form.acceptance.data = True

    delete_action.delete_retailer()

    delete_action_mocks.delete_polaris_retailer_data.assert_called_once()
    delete_action_mocks.delete_vela_retailer_data.assert_called_once()
    delete_action_mocks.delete_carina_retailer_data.assert_called_once()
    delete_action_mocks.delete_hubble_retailer_data.assert_called_once()

    for field in db_sessions_mocks:
        field.commit.assert_called_once()
        field.rollback.assert_not_called()

    mocked_flash.assert_called_once_with(
        f"All rows related to retailer {test_session_data.value.retailer_name} "
        f"({test_session_data.value.polaris_retailer_id}) have been deleted."
    )
    mocked_logger.exception.assert_not_called()


def test_delete_retailer_ok_user_disagreed(
    mocker: MockerFixture,
    delete_action: DeleteRetailerAction,
    test_session_data: SessionTestData,
    db_sessions_mocks: DBSessionsMocks,
    delete_action_mocks: DeleteActionMockedDBCalls,
) -> None:
    assert delete_action.validate_selected_ids(["1"]) is None
    assert delete_action.session_data == test_session_data.value
    delete_action_mocks.get_retailer_by_id.assert_called_once_with(1)

    mocked_flash = mocker.patch("event_horizon.polaris.custom_actions.flash")
    mocked_logger = mocker.patch.object(delete_action, "logger")
    delete_action.form.acceptance.data = False

    delete_action.delete_retailer()

    delete_action_mocks.delete_polaris_retailer_data.assert_not_called()
    delete_action_mocks.delete_vela_retailer_data.assert_not_called()
    delete_action_mocks.delete_carina_retailer_data.assert_not_called()
    delete_action_mocks.delete_hubble_retailer_data.assert_not_called()

    for field in db_sessions_mocks:
        field.commit.assert_not_called()
        field.rollback.assert_not_called()

    mocked_flash.assert_called_once_with("User did not agree to proceed, action halted.")
    mocked_logger.exception.assert_not_called()


def test_delete_retailer_db_error(
    mocker: MockerFixture,
    delete_action: DeleteRetailerAction,
    test_session_data: SessionTestData,
    db_sessions_mocks: DBSessionsMocks,
    delete_action_mocks: DeleteActionMockedDBCalls,
) -> None:
    assert delete_action.validate_selected_ids(["1"]) is None
    assert delete_action.session_data == test_session_data.value
    delete_action_mocks.get_retailer_by_id.assert_called_once_with(1)

    mocked_flash = mocker.patch("event_horizon.polaris.custom_actions.flash")
    mocked_logger = mocker.patch.object(delete_action, "logger")
    delete_action_mocks.delete_carina_retailer_data.side_effect = DataError("test error", [], None)
    delete_action.form.acceptance.data = True

    delete_action.delete_retailer()

    delete_action_mocks.delete_polaris_retailer_data.assert_called_once()
    delete_action_mocks.delete_vela_retailer_data.assert_called_once()
    delete_action_mocks.delete_carina_retailer_data.assert_called_once()
    delete_action_mocks.delete_hubble_retailer_data.assert_not_called()

    for field in db_sessions_mocks:
        field.commit.assert_not_called()
        field.rollback.assert_called_once()

    mocked_flash.assert_called_once_with("Something went wrong, database changes rolled back", category="error")
    mocked_logger.exception.assert_called_once()
