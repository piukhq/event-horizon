import base64
import pickle

from dataclasses import dataclass
from typing import Generator
from unittest.mock import MagicMock

import pytest

from flask import Flask
from pytest_mock import MockerFixture
from sqlalchemy.orm import Session

from app.vela.custom_actions import CampaignEndAction, CampaignRow, SessionFormData


@dataclass
class TestSessionFormData:
    value: SessionFormData
    b64str: str


@dataclass
class EndActionMockedCalls:
    balance_transfer: MagicMock
    update_end_date: MagicMock
    slug_and_goal: MagicMock
    status_change_fn: MagicMock


@pytest.fixture
def test_session_form_data() -> TestSessionFormData:
    session_form_data = SessionFormData(
        active_campaigns=[
            CampaignRow(id=1, slug="test-active-1", type="STAMPS"),
            CampaignRow(id=2, slug="test-active-2", type="STAMPS"),
            CampaignRow(id=3, slug="test-active-3", type="ACCUMULATOR"),
        ],
        draft_campaign=CampaignRow(id=4, slug="test-draft", type="STAMPS"),
        transfer_balance_from_choices=[
            (1, "test-active-1"),
            (2, "test-active-2"),
        ],
        optional_fields_needed=True,
    )

    return TestSessionFormData(
        value=session_form_data,
        b64str=base64.b64encode(pickle.dumps(session_form_data)).decode(),
    )


@pytest.fixture
def test_session_form_data_no_draft() -> TestSessionFormData:
    session_form_data = SessionFormData(
        active_campaigns=[CampaignRow(id=1, slug="test", type="STAMPS")],
        draft_campaign=None,
        transfer_balance_from_choices=[],
        optional_fields_needed=False,
    )
    return TestSessionFormData(
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
        balance_transfer=mocker.patch("app.vela.custom_actions.balance_transfer"),
        update_end_date=mocker.patch.object(end_action, "_update_from_campaign_end_date"),
        slug_and_goal=mocker.patch.object(end_action, "_get_from_campaign_slug_and_goal"),
        status_change_fn=MagicMock(),
    )
    mocks.status_change_fn.return_value = True
    mocks.slug_and_goal.return_value = ("test-active-1", 300)

    return mocks


def test_session_form_data_methods(test_session_form_data: TestSessionFormData) -> None:
    assert test_session_form_data.value.to_base64_str() == test_session_form_data.b64str
    assert SessionFormData.from_base64_str(test_session_form_data.b64str) == test_session_form_data.value


def test_campaign_end_action_session_form_data(
    end_action: CampaignEndAction, test_session_form_data: TestSessionFormData
) -> None:

    with pytest.raises(ValueError) as ex_info:
        end_action.session_form_data  # pylint: disable=pointless-statement

    assert ex_info.value.args[0] == (
        "validate_selected_campaigns or update_form must be called before accessing session_form_data"
    )

    end_action.update_form(test_session_form_data.b64str)
    assert end_action.session_form_data == test_session_form_data.value


def test_campaign_end_action_update_form_ok(
    end_action: CampaignEndAction, test_session_form_data: TestSessionFormData
) -> None:

    end_action.update_form(test_session_form_data.b64str)
    assert end_action.session_form_data == test_session_form_data.value

    for field_name in end_action.form_optional_fields:
        assert hasattr(end_action.form, field_name)


def test_campaign_end_action_update_form_session_form_data_already_set(
    end_action: CampaignEndAction, test_session_form_data: TestSessionFormData, mocker: MockerFixture
) -> None:
    mock_load_from_str = mocker.patch.object(SessionFormData, "from_base64_str")
    end_action._session_form_data = test_session_form_data.value
    end_action.update_form(test_session_form_data.b64str)
    mock_load_from_str.assert_not_called()


def test_campaign_end_action_update_form_no_draft_ok(
    end_action: CampaignEndAction, test_session_form_data_no_draft: TestSessionFormData
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
    end_action: CampaignEndAction, test_session_form_data: TestSessionFormData, mocker: MockerFixture
) -> None:
    mock_campaigns_rows = [
        MagicMock(id=1, slug="test-active-1", loyalty_type="STAMPS", status="ACTIVE", retailer_id=1),
        MagicMock(id=2, slug="test-active-2", loyalty_type="STAMPS", status="ACTIVE", retailer_id=1),
        MagicMock(id=3, slug="test-active-3", loyalty_type="ACCUMULATOR", status="ACTIVE", retailer_id=1),
        MagicMock(id=4, slug="test-draft", loyalty_type="STAMPS", status="DRAFT", retailer_id=1),
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
    mock_flash = mocker.patch("app.vela.custom_actions.flash")

    with pytest.raises(ValueError) as ex_info:
        end_action.validate_selected_campaigns(selected_campaigns)

    mock_get_campaigns_rows.assert_called_once_with(selected_campaigns)
    assert ex_info.value.args[0] == "failed validation"
    assert mock_flash.call_count == 2
    assert mock_flash.call_args_list[0].args[0] == "No campaign found."
    assert mock_flash.call_args_list[0].kwargs == {"category": "error"}
    assert mock_flash.call_args_list[1].args[0] == "At least one ACTIVE campaign must be provided."
    assert mock_flash.call_args_list[1].kwargs == {"category": "error"}


def test_campaign_end_action_validate_selected_campaigns_too_many_draft(
    end_action: CampaignEndAction, mocker: MockerFixture
) -> None:
    mock_campaigns_rows = [
        MagicMock(id=1, slug="test-active-1", loyalty_type="STAMPS", status="ACTIVE", retailer_id=1),
        MagicMock(id=2, slug="test-active-2", loyalty_type="ACCUMULATOR", status="ACTIVE", retailer_id=1),
        MagicMock(id=3, slug="test-draft-1", loyalty_type="ACCUMULATOR", status="DRAFT", retailer_id=1),
        MagicMock(id=4, slug="test-draft-2", loyalty_type="STAMPS", status="DRAFT", retailer_id=1),
    ]
    mock_get_campaigns_rows = mocker.patch.object(end_action, "_get_campaign_rows", return_value=mock_campaigns_rows)
    selected_campaigns = ["these", "values", "are", "ignored", "because", "of", "mock"]
    mock_flash = mocker.patch("app.vela.custom_actions.flash")

    with pytest.raises(ValueError) as ex_info:
        end_action.validate_selected_campaigns(selected_campaigns)

    mock_get_campaigns_rows.assert_called_once_with(selected_campaigns)
    assert ex_info.value.args[0] == "failed validation"
    mock_flash.assert_called_once_with("Only up to one DRAFT campaign allowed.", category="error")


def test_campaign_end_action_validate_selected_campaigns_different_retailer(
    end_action: CampaignEndAction, mocker: MockerFixture
) -> None:
    mock_campaigns_rows = [
        MagicMock(id=1, slug="test-active-1", loyalty_type="STAMPS", status="ACTIVE", retailer_id=1),
        MagicMock(id=2, slug="test-active-2", loyalty_type="ACCUMULATOR", status="ACTIVE", retailer_id=2),
    ]
    mock_get_campaigns_rows = mocker.patch.object(end_action, "_get_campaign_rows", return_value=mock_campaigns_rows)
    selected_campaigns = ["these", "values", "are", "ignored", "because", "of", "mock"]
    mock_flash = mocker.patch("app.vela.custom_actions.flash")

    with pytest.raises(ValueError) as ex_info:
        end_action.validate_selected_campaigns(selected_campaigns)

    mock_get_campaigns_rows.assert_called_once_with(selected_campaigns)
    assert ex_info.value.args[0] == "failed validation"
    mock_flash.assert_called_once_with("Selected campaigns must belong to the same retailer", category="error")


def test_campaign_end_action_validate_selected_campaigns_wrong_status(
    end_action: CampaignEndAction, mocker: MockerFixture
) -> None:
    mock_campaigns_rows = [
        MagicMock(id=1, slug="test-active-1", loyalty_type="STAMPS", status="ACTIVE", retailer_id=1),
        MagicMock(id=2, slug="test-active-2", loyalty_type="ACCUMULATOR", status="ENDED", retailer_id=1),
    ]
    mock_get_campaigns_rows = mocker.patch.object(end_action, "_get_campaign_rows", return_value=mock_campaigns_rows)
    selected_campaigns = ["these", "values", "are", "ignored", "because", "of", "mock"]
    mock_flash = mocker.patch("app.vela.custom_actions.flash")

    with pytest.raises(ValueError) as ex_info:
        end_action.validate_selected_campaigns(selected_campaigns)

    mock_get_campaigns_rows.assert_called_once_with(selected_campaigns)
    assert ex_info.value.args[0] == "failed validation"
    mock_flash.assert_called_once_with("Only ACTIVE or DRAFT campaigns allowed for this action.", category="error")


def test_campaign_end_action_end_campaigns_ok(
    end_action: CampaignEndAction, test_session_form_data: TestSessionFormData, end_action_mocks: EndActionMockedCalls
) -> None:
    assert test_session_form_data.value.draft_campaign, "using wrong fixture"

    convert_pending = False
    transfer_balance_from = 1
    convert_rate = 100
    qualify_threshold = 0

    end_action._session_form_data = test_session_form_data.value
    end_action.update_form("")
    end_action.form.transfer_balance.data = True
    end_action.form.transfer_balance_from.data = transfer_balance_from
    end_action.form.convert_rate.data = convert_rate
    end_action.form.qualify_threshold.data = qualify_threshold
    end_action.form.convert_pending_rewards.data = convert_pending

    end_action.end_campaigns(end_action_mocks.status_change_fn)

    assert end_action_mocks.status_change_fn.call_count == 2
    assert end_action_mocks.status_change_fn.call_args_list[0].args == (
        [test_session_form_data.value.draft_campaign.id],
        "active",
    )
    assert end_action_mocks.status_change_fn.call_args_list[1].args == (
        [cmp.id for cmp in test_session_form_data.value.active_campaigns],
        "ended",
    )
    assert end_action_mocks.status_change_fn.call_args_list[1].kwargs == {"issue_pending_rewards": convert_pending}
    end_action_mocks.update_end_date.assert_called_once_with()
    end_action_mocks.balance_transfer.assert_called_once_with(
        from_campaign_slug=test_session_form_data.value.active_campaigns[0].slug,
        to_campaign_slug=test_session_form_data.value.draft_campaign.slug,
        min_balance=int((300 / 100) * qualify_threshold),
        rate_percent=convert_rate,
        loyalty_type=test_session_form_data.value.draft_campaign.type,
    )
    end_action_mocks.slug_and_goal.assert_called_once_with(transfer_balance_from)


def test_campaign_end_action_end_campaigns_no_draft_ok(
    end_action: CampaignEndAction,
    test_session_form_data_no_draft: TestSessionFormData,
    end_action_mocks: EndActionMockedCalls,
) -> None:

    convert_pending = False

    end_action._session_form_data = test_session_form_data_no_draft.value
    end_action.update_form("")
    end_action.form.convert_pending_rewards.data = convert_pending

    end_action.end_campaigns(end_action_mocks.status_change_fn)

    end_action_mocks.status_change_fn.assert_called_once_with(
        [cmp.id for cmp in test_session_form_data_no_draft.value.active_campaigns],
        "ended",
        issue_pending_rewards=convert_pending,
    )

    end_action_mocks.update_end_date.assert_not_called()
    end_action_mocks.balance_transfer.assert_not_called()
    end_action_mocks.slug_and_goal.assert_not_called()


def test_campaign_end_action_end_campaigns_no_transfer_ok(
    end_action: CampaignEndAction, test_session_form_data: TestSessionFormData, end_action_mocks: EndActionMockedCalls
) -> None:
    assert test_session_form_data.value.draft_campaign, "using wrong fixture"

    convert_pending = False

    end_action._session_form_data = test_session_form_data.value
    end_action.update_form("")
    end_action.form.transfer_balance.data = False
    end_action.form.transfer_balance_from.data = 1
    end_action.form.convert_rate.data = 100
    end_action.form.qualify_threshold.data = 0
    end_action.form.convert_pending_rewards.data = convert_pending

    end_action.end_campaigns(end_action_mocks.status_change_fn)

    assert end_action_mocks.status_change_fn.call_count == 2
    assert end_action_mocks.status_change_fn.call_args_list[0].args == (
        [test_session_form_data.value.draft_campaign.id],
        "active",
    )
    assert end_action_mocks.status_change_fn.call_args_list[1].args == (
        [cmp.id for cmp in test_session_form_data.value.active_campaigns],
        "ended",
    )
    assert end_action_mocks.status_change_fn.call_args_list[1].kwargs == {"issue_pending_rewards": convert_pending}

    end_action_mocks.update_end_date.assert_not_called()
    end_action_mocks.balance_transfer.assert_not_called()
    end_action_mocks.slug_and_goal.assert_not_called()


def test_campaign_end_action_end_campaigns_transfer_balance_but_no_transfer_from_error(
    end_action: CampaignEndAction, test_session_form_data: TestSessionFormData, end_action_mocks: EndActionMockedCalls
) -> None:

    end_action._session_form_data = test_session_form_data.value
    end_action.update_form("")
    end_action._session_form_data.draft_campaign = None

    end_action.form.transfer_balance.data = True
    end_action.form.transfer_balance_from.data = 1
    end_action.form.convert_rate.data = 100
    end_action.form.qualify_threshold.data = 0
    end_action.form.convert_pending_rewards.data = False

    with pytest.raises(ValueError) as exc_info:
        end_action.end_campaigns(end_action_mocks.status_change_fn)

    assert exc_info.value.args[0] == "unexpected: no draft campaign found"
    end_action_mocks.status_change_fn.assert_not_called()
    end_action_mocks.update_end_date.assert_not_called()
    end_action_mocks.balance_transfer.assert_not_called()
    end_action_mocks.slug_and_goal.assert_not_called()


def test_campaign_end_action_end_campaigns_cant_fetch_from_campaign_error(
    end_action: CampaignEndAction, test_session_form_data: TestSessionFormData, end_action_mocks: EndActionMockedCalls
) -> None:
    assert test_session_form_data.value.draft_campaign, "using wrong fixture"

    end_action_mocks.slug_and_goal.return_value = None

    transfer_balance_from = 1
    convert_rate = 100
    qualify_threshold = 0

    end_action._session_form_data = test_session_form_data.value
    end_action.update_form("")

    end_action.form.transfer_balance.data = True
    end_action.form.transfer_balance_from.data = transfer_balance_from
    end_action.form.convert_rate.data = convert_rate
    end_action.form.qualify_threshold.data = qualify_threshold
    end_action.form.convert_pending_rewards.data = False

    with pytest.raises(ValueError) as exc_info:
        end_action.end_campaigns(end_action_mocks.status_change_fn)

    assert (
        exc_info.value.args[0]
        == f"Could not find Campaign.slug and RewardRule.reward_goal for campaign of id: {transfer_balance_from}"
    )
    end_action_mocks.status_change_fn.assert_called_once_with(
        [test_session_form_data.value.draft_campaign.id], "active"
    )
    end_action_mocks.update_end_date.assert_called_once_with()
    end_action_mocks.balance_transfer.assert_not_called()
    end_action_mocks.slug_and_goal.assert_called_once_with(transfer_balance_from)


def test_campaign_end_action_end_campaigns_failed_status_change_error(
    end_action: CampaignEndAction, test_session_form_data: TestSessionFormData, end_action_mocks: EndActionMockedCalls
) -> None:
    assert test_session_form_data.value.draft_campaign, "using wrong fixture"

    end_action_mocks.status_change_fn.return_value = False

    end_action._session_form_data = test_session_form_data.value
    end_action.update_form("")

    end_action.form.transfer_balance.data = True
    end_action.form.transfer_balance_from.data = 1
    end_action.form.convert_rate.data = 100
    end_action.form.qualify_threshold.data = 0
    end_action.form.convert_pending_rewards.data = False

    end_action.end_campaigns(end_action_mocks.status_change_fn)

    end_action_mocks.status_change_fn.assert_called_once_with(
        [test_session_form_data.value.draft_campaign.id], "active"
    )
    end_action_mocks.update_end_date.assert_not_called()
    end_action_mocks.balance_transfer.assert_not_called()
    end_action_mocks.slug_and_goal.assert_not_called()
