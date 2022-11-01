import base64
import pickle

from dataclasses import dataclass
from typing import Generator
from unittest.mock import ANY, MagicMock

import pytest

from flask import Flask
from pytest_mock import MockerFixture
from sqlalchemy.orm import Session

from event_horizon.vela.custom_actions import CampaignEndAction, CampaignRow, SessionFormData
from event_horizon.vela.enums import PendingRewardChoices


@dataclass
class SessionFormTestData:
    value: SessionFormData
    b64str: str


@dataclass
class EndActionMockedCalls:
    transfer_balance: MagicMock
    transfer_pending_rewards: MagicMock
    update_end_date: MagicMock
    status_change_fn: MagicMock


@pytest.fixture
def test_session_form_data() -> SessionFormTestData:
    session_form_data = SessionFormData(
        retailer_slug="test-retailer",
        active_campaign=CampaignRow(
            id=1, slug="test-active", type="STAMPS", reward_goal=100, reward_slug="test-reward-active"
        ),
        draft_campaign=CampaignRow(
            id=2, slug="test-draft", type="STAMPS", reward_goal=100, reward_slug="test-reward-draft"
        ),
        optional_fields_needed=True,
    )

    return SessionFormTestData(
        value=session_form_data,
        b64str=base64.b64encode(pickle.dumps(session_form_data)).decode(),
    )


@pytest.fixture
def test_session_form_data_no_draft() -> SessionFormTestData:
    session_form_data = SessionFormData(
        retailer_slug="test-retailer",
        active_campaign=CampaignRow(id=1, slug="test", type="STAMPS", reward_goal=100, reward_slug="test-reward"),
        draft_campaign=None,
        optional_fields_needed=False,
    )
    return SessionFormTestData(
        value=session_form_data,
        b64str=base64.b64encode(pickle.dumps(session_form_data)).decode(),
    )


@pytest.fixture
def end_action() -> Generator[CampaignEndAction, None, None]:
    app = Flask(__name__)
    app.secret_key = "random string"
    with app.app_context(), app.test_request_context():
        yield CampaignEndAction(MagicMock(spec=Session))


@pytest.fixture
def end_action_mocks(mocker: MockerFixture, end_action: CampaignEndAction) -> EndActionMockedCalls:
    mocks = EndActionMockedCalls(
        transfer_balance=mocker.patch("event_horizon.vela.custom_actions.transfer_balance"),
        transfer_pending_rewards=mocker.patch("event_horizon.vela.custom_actions.transfer_pending_rewards"),
        update_end_date=mocker.patch.object(end_action, "_update_from_campaign_end_date"),
        status_change_fn=MagicMock(),
    )
    mocks.status_change_fn.return_value = True

    return mocks


def test_session_form_data_methods(test_session_form_data: SessionFormTestData) -> None:
    assert test_session_form_data.value.to_base64_str() == test_session_form_data.b64str
    assert SessionFormData.from_base64_str(test_session_form_data.b64str) == test_session_form_data.value


def test_campaign_end_action_session_form_data(
    end_action: CampaignEndAction, test_session_form_data: SessionFormTestData
) -> None:

    with pytest.raises(ValueError) as ex_info:
        end_action.session_form_data  # pylint: disable=pointless-statement

    assert ex_info.value.args[0] == (
        "validate_selected_campaigns or update_form must be called before accessing session_form_data"
    )

    end_action.update_form(test_session_form_data.b64str)
    assert end_action.session_form_data == test_session_form_data.value


def test_campaign_end_action_update_form_ok(
    end_action: CampaignEndAction, test_session_form_data: SessionFormTestData
) -> None:

    end_action.update_form(test_session_form_data.b64str)
    assert end_action.session_form_data == test_session_form_data.value

    for field_name in end_action.form_optional_fields:
        assert hasattr(end_action.form, field_name)


def test_campaign_end_action_update_form_session_form_data_already_set(
    end_action: CampaignEndAction, test_session_form_data: SessionFormTestData, mocker: MockerFixture
) -> None:
    mock_load_from_str = mocker.patch.object(SessionFormData, "from_base64_str")
    end_action._session_form_data = test_session_form_data.value
    end_action.update_form(test_session_form_data.b64str)
    mock_load_from_str.assert_not_called()


def test_campaign_end_action_update_form_no_draft_ok(
    end_action: CampaignEndAction, test_session_form_data_no_draft: SessionFormTestData
) -> None:
    end_action.update_form(test_session_form_data_no_draft.b64str)
    assert end_action.session_form_data == test_session_form_data_no_draft.value
    assert end_action.session_form_data.to_base64_str() == test_session_form_data_no_draft.b64str

    for field_name in end_action.form_optional_fields:
        assert not getattr(end_action.form, field_name, None)


def test_campaign_end_action_update_form_invalid_str(end_action: CampaignEndAction) -> None:
    with pytest.raises(ValueError) as ex_info:
        end_action.update_form("not a base64 string")

    assert not end_action._session_form_data
    assert ex_info.value.args[0] == "unexpected value found for 'form_dynamic_values'"


def test_campaign_end_action_update_form_invalid_content(end_action: CampaignEndAction) -> None:
    with pytest.raises(TypeError) as ex_info:
        end_action.update_form(base64.b64encode(pickle.dumps({"value": "not SessionFormData"})).decode())

    assert not end_action._session_form_data
    assert ex_info.value.args[0] == "'form_dynamic_values' is not a valid SessionFormData"


def test_campaign_end_action_validate_selected_campaigns_ok(
    end_action: CampaignEndAction, test_session_form_data: SessionFormTestData, mocker: MockerFixture
) -> None:

    mock_campaigns_rows = [
        MagicMock(
            id=1,
            slug="test-active",
            loyalty_type="STAMPS",
            status="ACTIVE",
            retailer_slug="test-retailer",
            reward_goal=100,
            reward_slug="test-reward-active",
        ),
        MagicMock(
            id=2,
            slug="test-draft",
            loyalty_type="STAMPS",
            status="DRAFT",
            retailer_slug="test-retailer",
            reward_goal=100,
            reward_slug="test-reward-draft",
        ),
    ]
    mock_get_campaigns_rows = mocker.patch.object(end_action, "_get_campaign_rows", return_value=mock_campaigns_rows)
    selected_campaigns = ["these", "values", "are", "ignored", "because", "of", "mock"]

    end_action.validate_selected_campaigns(selected_campaigns)

    mock_get_campaigns_rows.assert_called_once_with(selected_campaigns)
    assert end_action.session_form_data == test_session_form_data.value


def test_campaign_end_action_validate_selected_campaigns_no_campaign_found(
    end_action: CampaignEndAction, mocker: MockerFixture
) -> None:
    mock_campaigns_rows: list = []
    mock_get_campaigns_rows = mocker.patch.object(end_action, "_get_campaign_rows", return_value=mock_campaigns_rows)
    selected_campaigns = ["these", "values", "are", "ignored", "because", "of", "mock"]
    mock_flash = mocker.patch("event_horizon.vela.custom_actions.flash")

    with pytest.raises(ValueError) as ex_info:
        end_action.validate_selected_campaigns(selected_campaigns)

    mock_get_campaigns_rows.assert_called_once_with(selected_campaigns)
    assert ex_info.value.args[0] == "failed validation"
    assert mock_flash.call_count == 2
    assert mock_flash.call_args_list[0].args[0] == "No campaign found."
    assert mock_flash.call_args_list[0].kwargs == {"category": "error"}
    assert mock_flash.call_args_list[1].args[0] == "One ACTIVE campaign must be provided."
    assert mock_flash.call_args_list[1].kwargs == {"category": "error"}


def test_campaign_end_action_validate_selected_campaigns_too_many_draft(
    end_action: CampaignEndAction, mocker: MockerFixture
) -> None:
    mock_campaigns_rows = [
        MagicMock(
            id=1,
            slug="test-active-1",
            loyalty_type="STAMPS",
            status="ACTIVE",
            retailer_slug="test-retailer",
            reward_goal=100,
            reward_slug="test-reward-active",
        ),
        MagicMock(
            id=2,
            slug="test-draft-1",
            loyalty_type="STAMPS",
            status="DRAFT",
            retailer_slug="test-retailer",
            reward_goal=100,
            reward_slug="test-reward-draft-1",
        ),
        MagicMock(
            id=3,
            slug="test-draft-2",
            loyalty_type="STAMPS",
            status="DRAFT",
            retailer_slug="test-retailer",
            reward_goal=100,
            reward_slug="test-reward-draft-2",
        ),
    ]
    mock_get_campaigns_rows = mocker.patch.object(end_action, "_get_campaign_rows", return_value=mock_campaigns_rows)
    selected_campaigns = ["these", "values", "are", "ignored", "because", "of", "mock"]
    mock_flash = mocker.patch("event_horizon.vela.custom_actions.flash")

    with pytest.raises(ValueError) as ex_info:
        end_action.validate_selected_campaigns(selected_campaigns)

    mock_get_campaigns_rows.assert_called_once_with(selected_campaigns)
    assert ex_info.value.args[0] == "failed validation"
    mock_flash.assert_called_once_with("Only up to one DRAFT and one ACTIVE campaign allowed.", category="error")


def test_campaign_end_action_validate_selected_campaigns_too_many_active(
    end_action: CampaignEndAction, mocker: MockerFixture
) -> None:
    mock_campaigns_rows = [
        MagicMock(
            id=1,
            slug="test-active-1",
            loyalty_type="STAMPS",
            status="ACTIVE",
            retailer_slug="test-retailer",
            reward_goal=100,
            reward_slug="test-reward-active-1",
        ),
        MagicMock(
            id=2,
            slug="test-active-2",
            loyalty_type="STAMPS",
            status="DRAFT",
            retailer_slug="test-retailer",
            reward_goal=100,
            reward_slug="test-reward-active-2",
        ),
        MagicMock(
            id=3,
            slug="test-draft",
            loyalty_type="STAMPS",
            status="DRAFT",
            retailer_slug="test-retailer",
            reward_goal=100,
            reward_slug="test-reward-draft",
        ),
    ]
    mock_get_campaigns_rows = mocker.patch.object(end_action, "_get_campaign_rows", return_value=mock_campaigns_rows)
    selected_campaigns = ["these", "values", "are", "ignored", "because", "of", "mock"]
    mock_flash = mocker.patch("event_horizon.vela.custom_actions.flash")

    with pytest.raises(ValueError) as ex_info:
        end_action.validate_selected_campaigns(selected_campaigns)

    mock_get_campaigns_rows.assert_called_once_with(selected_campaigns)
    assert ex_info.value.args[0] == "failed validation"
    mock_flash.assert_called_once_with("Only up to one DRAFT and one ACTIVE campaign allowed.", category="error")


def test_campaign_end_action_validate_selected_campaigns_different_retailer(
    end_action: CampaignEndAction, mocker: MockerFixture
) -> None:
    mock_campaigns_rows = [
        MagicMock(
            id=1,
            slug="test-active",
            loyalty_type="STAMPS",
            status="ACTIVE",
            retailer_slug="test-retailer-1",
            reward_goal=100,
            reward_slug="test-reward-active",
        ),
        MagicMock(
            id=2,
            slug="test-draft",
            loyalty_type="STAMPS",
            status="DRAFT",
            retailer_slug="test-retailer-2",
            reward_goal=100,
            reward_slug="test-reward-draft",
        ),
    ]
    mock_get_campaigns_rows = mocker.patch.object(end_action, "_get_campaign_rows", return_value=mock_campaigns_rows)
    selected_campaigns = ["these", "values", "are", "ignored", "because", "of", "mock"]
    mock_flash = mocker.patch("event_horizon.vela.custom_actions.flash")

    with pytest.raises(ValueError) as ex_info:
        end_action.validate_selected_campaigns(selected_campaigns)

    mock_get_campaigns_rows.assert_called_once_with(selected_campaigns)
    assert ex_info.value.args[0] == "failed validation"
    mock_flash.assert_called_once_with("Selected campaigns must belong to the same retailer.", category="error")


def test_campaign_end_action_validate_selected_campaigns_wrong_status(
    end_action: CampaignEndAction, mocker: MockerFixture
) -> None:
    mock_campaigns_rows = [
        MagicMock(
            id=1,
            slug="test-active",
            loyalty_type="ACCUMULATOR",
            status="ACTIVE",
            retailer_slug="test-retailer",
            reward_goal=100,
            reward_slug="test-reward-active",
        ),
        MagicMock(
            id=2,
            slug="test-endend",
            loyalty_type="ACCUMULATOR",
            status="ENDED",
            retailer_slug="test-retailer",
            reward_goal=100,
            reward_slug="test-reward-ended",
        ),
    ]
    mock_get_campaigns_rows = mocker.patch.object(end_action, "_get_campaign_rows", return_value=mock_campaigns_rows)
    selected_campaigns = ["these", "values", "are", "ignored", "because", "of", "mock"]
    mock_flash = mocker.patch("event_horizon.vela.custom_actions.flash")

    with pytest.raises(ValueError) as ex_info:
        end_action.validate_selected_campaigns(selected_campaigns)

    mock_get_campaigns_rows.assert_called_once_with(selected_campaigns)
    assert ex_info.value.args[0] == "failed validation"
    mock_flash.assert_called_once_with("Only ACTIVE or DRAFT campaigns allowed for this action.", category="error")


def test_campaign_end_action_validate_selected_campaigns_different_loyalty_type(
    end_action: CampaignEndAction, mocker: MockerFixture
) -> None:
    mock_campaigns_rows = [
        MagicMock(
            id=1,
            slug="test-active",
            loyalty_type="STAMPS",
            status="ACTIVE",
            retailer_slug="test-retailer",
            reward_goal=100,
            reward_slug="test-reward-active",
        ),
        MagicMock(
            id=2,
            slug="test-draft",
            loyalty_type="ACCUMULATOR",
            status="DRAFT",
            retailer_slug="test-retailer",
            reward_goal=100,
            reward_slug="test-reward-draft",
        ),
    ]
    mock_get_campaigns_rows = mocker.patch.object(end_action, "_get_campaign_rows", return_value=mock_campaigns_rows)
    selected_campaigns = ["these", "values", "are", "ignored", "because", "of", "mock"]
    mock_flash = mocker.patch("event_horizon.vela.custom_actions.flash")

    with pytest.raises(ValueError) as ex_info:
        end_action.validate_selected_campaigns(selected_campaigns)

    mock_get_campaigns_rows.assert_called_once_with(selected_campaigns)
    assert ex_info.value.args[0] == "failed validation"
    mock_flash.assert_called_once_with("Selected campaigns must have the same loyalty type.", category="error")


def test_campaign_end_action_end_campaigns_ok(
    end_action: CampaignEndAction,
    test_session_form_data: SessionFormTestData,
    end_action_mocks: EndActionMockedCalls,
    mocker: "MockerFixture",
) -> None:
    assert test_session_form_data.value.draft_campaign, "using wrong fixture"

    mock_send_activity = mocker.patch("event_horizon.vela.custom_actions.sync_send_activity")

    convert_rate = 100
    qualify_threshold = 0

    end_action._session_form_data = test_session_form_data.value
    end_action.update_form("")
    end_action.form.transfer_balance.data = True
    end_action.form.convert_rate.data = convert_rate
    end_action.form.qualify_threshold.data = qualify_threshold
    end_action.form.handle_pending_rewards.data = PendingRewardChoices.TRANSFER

    end_action.end_campaigns(end_action_mocks.status_change_fn)

    assert end_action_mocks.status_change_fn.call_count == 2
    assert end_action_mocks.status_change_fn.call_args_list[0].args == (
        [test_session_form_data.value.draft_campaign.id],
        "active",
    )
    assert end_action_mocks.status_change_fn.call_args_list[1].args == (
        [test_session_form_data.value.active_campaign.id],
        "ended",
    )
    assert end_action_mocks.status_change_fn.call_args_list[1].kwargs == {"issue_pending_rewards": False}
    end_action_mocks.update_end_date.assert_called_once_with()
    end_action_mocks.transfer_pending_rewards.assert_called_once_with(
        ANY,  # this is the db_session
        from_campaign_slug=test_session_form_data.value.active_campaign.slug,
        to_campaign_slug=test_session_form_data.value.draft_campaign.slug,
        to_campaign_reward_slug=test_session_form_data.value.draft_campaign.reward_slug,
    )
    end_action_mocks.transfer_balance.assert_called_once_with(
        ANY,  # this is the db_session
        retailer_slug=test_session_form_data.value.retailer_slug,
        from_campaign_slug=test_session_form_data.value.active_campaign.slug,
        to_campaign_slug=test_session_form_data.value.draft_campaign.slug,
        min_balance=int((300 / 100) * qualify_threshold),
        rate_percent=convert_rate,
        loyalty_type=test_session_form_data.value.draft_campaign.type,
    )
    mock_send_activity.assert_called_once()


def test_campaign_end_action_end_campaigns_no_draft_ok(
    end_action: CampaignEndAction,
    test_session_form_data_no_draft: SessionFormTestData,
    end_action_mocks: EndActionMockedCalls,
) -> None:

    end_action._session_form_data = test_session_form_data_no_draft.value
    end_action.update_form("")
    end_action.form.handle_pending_rewards.data = PendingRewardChoices.REMOVE

    end_action.end_campaigns(end_action_mocks.status_change_fn)

    end_action_mocks.status_change_fn.assert_called_once_with(
        [test_session_form_data_no_draft.value.active_campaign.id],
        "ended",
        issue_pending_rewards=False,
    )

    end_action_mocks.update_end_date.assert_not_called()
    end_action_mocks.transfer_balance.assert_not_called()
    end_action_mocks.transfer_pending_rewards.assert_not_called()


def test_campaign_end_action_end_campaigns_no_transfer_ok(
    end_action: CampaignEndAction, test_session_form_data: SessionFormTestData, end_action_mocks: EndActionMockedCalls
) -> None:
    assert test_session_form_data.value.draft_campaign, "using wrong fixture"

    end_action._session_form_data = test_session_form_data.value
    end_action.update_form("")
    end_action.form.transfer_balance.data = False
    end_action.form.convert_rate.data = 100
    end_action.form.qualify_threshold.data = 0
    end_action.form.handle_pending_rewards.data = PendingRewardChoices.REMOVE

    end_action.end_campaigns(end_action_mocks.status_change_fn)

    assert end_action_mocks.status_change_fn.call_count == 2
    assert end_action_mocks.status_change_fn.call_args_list[0].args == (
        [test_session_form_data.value.draft_campaign.id],
        "active",
    )
    assert end_action_mocks.status_change_fn.call_args_list[1].args == (
        [test_session_form_data.value.active_campaign.id],
        "ended",
    )
    assert end_action_mocks.status_change_fn.call_args_list[1].kwargs == {"issue_pending_rewards": False}

    end_action_mocks.update_end_date.assert_not_called()
    end_action_mocks.transfer_balance.assert_not_called()
    end_action_mocks.transfer_pending_rewards.assert_not_called()


def test_campaign_end_action_end_campaigns_transfer_balance_but_no_draft_error(
    end_action: CampaignEndAction, test_session_form_data: SessionFormTestData, end_action_mocks: EndActionMockedCalls
) -> None:

    end_action._session_form_data = test_session_form_data.value
    end_action.update_form("")
    end_action._session_form_data.draft_campaign = None

    end_action.form.transfer_balance.data = True
    end_action.form.convert_rate.data = 100
    end_action.form.qualify_threshold.data = 0
    end_action.form.handle_pending_rewards.data = PendingRewardChoices.REMOVE

    with pytest.raises(ValueError) as exc_info:
        end_action.end_campaigns(end_action_mocks.status_change_fn)

    assert exc_info.value.args[0] == "unexpected: no draft campaign found"
    end_action_mocks.status_change_fn.assert_not_called()
    end_action_mocks.update_end_date.assert_not_called()
    end_action_mocks.transfer_balance.assert_not_called()
    end_action_mocks.transfer_pending_rewards.assert_not_called()


def test_campaign_end_action_end_campaigns_failed_status_change_error(
    end_action: CampaignEndAction, test_session_form_data: SessionFormTestData, end_action_mocks: EndActionMockedCalls
) -> None:
    assert test_session_form_data.value.draft_campaign, "using wrong fixture"

    end_action_mocks.status_change_fn.return_value = False

    end_action._session_form_data = test_session_form_data.value
    end_action.update_form("")

    end_action.form.transfer_balance.data = True
    end_action.form.convert_rate.data = 100
    end_action.form.qualify_threshold.data = 0
    end_action.form.handle_pending_rewards.data = PendingRewardChoices.REMOVE

    end_action.end_campaigns(end_action_mocks.status_change_fn)

    end_action_mocks.status_change_fn.assert_called_once_with(
        [test_session_form_data.value.draft_campaign.id], "active"
    )
    end_action_mocks.update_end_date.assert_not_called()
    end_action_mocks.transfer_balance.assert_not_called()
    end_action_mocks.transfer_pending_rewards.assert_not_called()
