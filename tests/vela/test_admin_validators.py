from unittest import mock

import pytest
import wtforms

from app.vela.validators import (
    validate_campaign_earn_inc_is_tx_value,
    validate_campaign_status_change,
    validate_earn_rule_deletion,
    validate_earn_rule_increment,
    validate_reward_rule_deletion,
)


@pytest.fixture
def mock_form() -> mock.MagicMock:
    return mock.MagicMock(spec=wtforms.Form)


@pytest.fixture
def mock_field() -> mock.MagicMock:
    return mock.MagicMock(spec=wtforms.Field)


def test_validate_earn_rule_increment__inc_is_tx_val__inc_has_val(
    mock_form: mock.MagicMock, mock_field: mock.MagicMock
) -> None:
    mock_form.campaign = mock.Mock(data=mock.Mock(earn_inc_is_tx_value=True))
    mock_field.data = 10

    with pytest.raises(wtforms.ValidationError) as ex_info:
        validate_earn_rule_increment(mock_form, mock_field)
    assert (
        ex_info.value.args[0]
        == "The campaign requires that this field is not populated due to campaign.earn_inc_is_tx_value setting"
    )


def test_validate_earn_rule_increment__inc_is_tx_val__inc_has_blank_val(
    mock_form: mock.MagicMock, mock_field: mock.MagicMock
) -> None:
    mock_form.campaign = mock.Mock(data=mock.Mock(earn_inc_is_tx_value=True))
    mock_field.data = None
    try:
        validate_earn_rule_increment(mock_form, mock_field)
    except Exception:
        pytest.fail()


def test_validate_earn_rule_increment__inc_is_not_tx_val__inc_has_val(
    mock_form: mock.MagicMock, mock_field: mock.MagicMock
) -> None:
    mock_form.campaign = mock.Mock(data=mock.Mock(earn_inc_is_tx_value=False))
    mock_field.data = 10

    try:
        validate_earn_rule_increment(mock_form, mock_field)
    except Exception:
        pytest.fail()


def test_validate_earn_rule_increment__inc_is_not_tx_val__inc_has_blank_val(
    mock_form: mock.MagicMock, mock_field: mock.MagicMock
) -> None:
    mock_form.campaign = mock.Mock(data=mock.Mock(earn_inc_is_tx_value=False))
    mock_field.data = None
    with pytest.raises(wtforms.validators.StopValidation) as ex_info:
        validate_earn_rule_increment(mock_form, mock_field)
    assert (
        ex_info.value.args[0]
        == "The campaign requires that this field is populated due to campaign.earn_inc_is_tx_value setting"
    )


@mock.patch("app.vela.validators._count_earn_rules")
def test_validate_campaign_earn_inc_is_tx_value__new_object(
    mock__count_earn_rules: mock.MagicMock, mock_form: mock.MagicMock, mock_field: mock.MagicMock
) -> None:
    mock_form._obj = None
    try:
        validate_campaign_earn_inc_is_tx_value(mock_form, mock_field)
    except Exception:
        pytest.fail()


@mock.patch("app.vela.validators._count_earn_rules")
def test_validate_campaign_earn_inc_is_tx_value__true__earn_rules_with_inc_val(
    mock__count_earn_rules: mock.MagicMock, mock_form: mock.MagicMock, mock_field: mock.MagicMock
) -> None:
    mock_form._obj = mock.Mock(id=1)
    mock_field.data = True
    mock__count_earn_rules.return_value = 10
    with pytest.raises(wtforms.ValidationError) as ex_info:
        validate_campaign_earn_inc_is_tx_value(mock_form, mock_field)
    assert ex_info.value.args[0] == "This field cannot be changed as there are earn rules with increment values"
    mock__count_earn_rules.assert_called_with(1, has_inc_value=True)


@mock.patch("app.vela.validators._count_earn_rules")
def test_validate_campaign_earn_inc_is_tx_value__false__earn_rules_with_inc_val(
    mock__count_earn_rules: mock.MagicMock, mock_form: mock.MagicMock, mock_field: mock.MagicMock
) -> None:
    mock_form._obj = mock.Mock(id=1)
    mock_field.data = False
    mock__count_earn_rules.return_value = 10
    with pytest.raises(wtforms.ValidationError) as ex_info:
        validate_campaign_earn_inc_is_tx_value(mock_form, mock_field)
    assert ex_info.value.args[0] == "This field cannot be changed as there are earn rules with null increments"
    mock__count_earn_rules.assert_called_with(1, has_inc_value=False)


@mock.patch("app.vela.validators._count_earn_rules")
def test_validate_campaign_earn_inc_is_tx_value__false__zero_earn_rules_with_inc_val(
    mock__count_earn_rules: mock.MagicMock, mock_form: mock.MagicMock, mock_field: mock.MagicMock
) -> None:
    mock_form._obj = mock.Mock(id=1)
    mock_field.data = False
    mock__count_earn_rules.return_value = 0
    try:
        validate_campaign_earn_inc_is_tx_value(mock_form, mock_field)
    except Exception:
        pytest.fail()
    mock__count_earn_rules.assert_called_with(1, has_inc_value=False)


@mock.patch("app.vela.validators._count_earn_rules")
def test_validate_campaign_earn_inc_is_tx_value__true__zero_earn_rules_with_inc_val(
    mock__count_earn_rules: mock.MagicMock, mock_form: mock.MagicMock, mock_field: mock.MagicMock
) -> None:
    mock_form._obj = mock.Mock(id=1)
    mock_field.data = True
    mock__count_earn_rules.return_value = 0
    try:
        validate_campaign_earn_inc_is_tx_value(mock_form, mock_field)
    except Exception:
        pytest.fail()
    mock__count_earn_rules.assert_called_with(1, has_inc_value=True)


@mock.patch("app.vela.validators._get_campaign_by_id")
def test_validate_campaign_status_change_all_good(
    mock_campaign: mock.MagicMock, mock_form: mock.MagicMock, mock_field: mock.MagicMock
) -> None:
    mock_form._obj = mock.Mock(id=1)
    mock_field.data = "ACTIVE"
    mock_campaign.return_value = mock.MagicMock(status="DRAFT", earnrule_collection=[1], rewardrule_collection=[1])

    validate_campaign_status_change(mock_form, mock_field)


@mock.patch("app.vela.validators._get_campaign_by_id")
def test_validate_campaign_status_change_no_rules(
    mock_campaign: mock.MagicMock, mock_form: mock.MagicMock, mock_field: mock.MagicMock
) -> None:
    mock_form._obj = mock.Mock(id=1)
    mock_field.data = "ACTIVE"
    mock_campaign.return_value = mock.MagicMock(status="DRAFT", earnrule_collection=[], rewardrule_collection=[])

    with pytest.raises(wtforms.ValidationError):
        validate_campaign_status_change(mock_form, mock_field)


@mock.patch("app.vela.validators._get_campaign_by_id")
def test_validate_campaign_status_change_no_earn_rules(
    mock_campaign: mock.MagicMock, mock_form: mock.MagicMock, mock_field: mock.MagicMock
) -> None:
    mock_form._obj = mock.Mock(id=1)
    mock_field.data = "ACTIVE"
    mock_campaign.return_value = mock.MagicMock(status="DRAFT", earnrule_collection=[], rewardrule_collection=[1])

    with pytest.raises(wtforms.ValidationError):
        validate_campaign_status_change(mock_form, mock_field)


@mock.patch("app.vela.validators._get_campaign_by_id")
def test_validate_campaign_status_change_no_reward_rule(
    mock_campaign: mock.MagicMock, mock_form: mock.MagicMock, mock_field: mock.MagicMock
) -> None:
    mock_form._obj = mock.Mock(id=1)
    mock_field.data = "ACTIVE"
    mock_campaign.return_value = mock.MagicMock(status="DRAFT", earnrule_collection=[1], rewardrule_collection=[])

    with pytest.raises(wtforms.ValidationError):
        validate_campaign_status_change(mock_form, mock_field)


@mock.patch("app.vela.validators._get_campaign_by_id")
def test_validate_campaign_status_change_already_active(
    mock_campaign: mock.MagicMock, mock_form: mock.MagicMock, mock_field: mock.MagicMock
) -> None:
    mock_form._obj = mock.Mock(id=1)
    mock_field.data = "ACTIVE"
    mock_campaign.return_value = mock.MagicMock(status="ACTIVE", earnrule_collection=[], rewardrule_collection=[])

    validate_campaign_status_change(mock_form, mock_field)


@mock.patch("app.vela.validators._get_campaign_by_id")
def test_validate_earn_rule_deletion_active_campaign_not_last_rule(mock_campaign: mock.MagicMock) -> None:
    mock_campaign.return_value = mock.MagicMock(status="ACTIVE", earnrule_collection=[1, 2], rewardrule_collection=[])

    validate_earn_rule_deletion(1)


@mock.patch("app.vela.validators._get_campaign_by_id")
def test_validate_earn_rule_deletion_active_campaign_last_rule(mock_campaign: mock.MagicMock) -> None:
    mock_campaign.return_value = mock.MagicMock(status="ACTIVE", earnrule_collection=[1], rewardrule_collection=[])

    with pytest.raises(wtforms.ValidationError):
        validate_earn_rule_deletion(1)


@mock.patch("app.vela.validators._get_campaign_by_id")
def test_validate_earn_rule_deletion_non_active_campaign(mock_campaign: mock.MagicMock) -> None:
    mock_campaign.return_value = mock.MagicMock(status="DRAFT", earnrule_collection=[1], rewardrule_collection=[])

    validate_earn_rule_deletion(1)


@mock.patch("app.vela.validators._get_campaign_by_id")
def test_validate_reward_rule_deletion_non_active_campaign(mock_campaign: mock.MagicMock) -> None:
    mock_campaign.return_value = mock.MagicMock(status="DRAFT", earnrule_collection=[], rewardrule_collection=[1])

    validate_reward_rule_deletion(1)


@mock.patch("app.vela.validators._get_campaign_by_id")
def test_validate_reward_rule_deletion_active_campaign(mock_campaign: mock.MagicMock) -> None:
    mock_campaign.return_value = mock.MagicMock(status="ACTIVE", earnrule_collection=[], rewardrule_collection=[1])

    with pytest.raises(wtforms.ValidationError):
        validate_reward_rule_deletion(1)
