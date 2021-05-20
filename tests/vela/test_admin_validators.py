from unittest import mock

import pytest
import wtforms

from app.vela.validators import validate_earn_rule_increment


@pytest.fixture
def mock_form() -> mock.MagicMock:
    return mock.MagicMock(spec=wtforms.Form)


@pytest.fixture
def mock_increment_field() -> mock.MagicMock:
    return mock.MagicMock(spec=wtforms.Field)


def test_validate_earn_rule_increment__inc_is_tx_val__inc_has_val(
    mock_form: mock.MagicMock, mock_increment_field: mock.MagicMock
) -> None:
    mock_form.campaign = mock.Mock(data=mock.Mock(earn_inc_is_tx_value=True))
    mock_increment_field.data = 10

    with pytest.raises(wtforms.ValidationError) as ex_info:
        validate_earn_rule_increment(mock_form, mock_increment_field)
    assert (
        ex_info.value.args[0]
        == "The campaign requires that this field is blank due to campaign.earn_inc_is_tx_value setting"
    )


def test_validate_earn_rule_increment__inc_is_tx_val__inc_has_blank_val(
    mock_form: mock.MagicMock, mock_increment_field: mock.MagicMock
) -> None:
    mock_form.campaign = mock.Mock(data=mock.Mock(earn_inc_is_tx_value=True))
    for val in (None, ""):
        mock_increment_field.data = val
        try:
            validate_earn_rule_increment(mock_form, mock_increment_field)
        except Exception:
            pytest.fail()


def test_validate_earn_rule_increment__inc_is_not_tx_val__inc_has_val(
    mock_form: mock.MagicMock, mock_increment_field: mock.MagicMock
) -> None:
    mock_form.campaign = mock.Mock(data=mock.Mock(earn_inc_is_tx_value=False))
    mock_increment_field.data = 10

    try:
        validate_earn_rule_increment(mock_form, mock_increment_field)
    except Exception:
        pytest.fail()


def test_validate_earn_rule_increment__inc_is_not_tx_val__inc_has_blank_val(
    mock_form: mock.MagicMock, mock_increment_field: mock.MagicMock
) -> None:
    mock_form.campaign = mock.Mock(data=mock.Mock(earn_inc_is_tx_value=False))
    for val in (None, ""):
        mock_increment_field.data = val
        with pytest.raises(wtforms.validators.StopValidation) as ex_info:
            validate_earn_rule_increment(mock_form, mock_increment_field)
        assert (
            ex_info.value.args[0]
            == "The campaign requires that this field is not blank due to campaign.earn_inc_is_tx_value setting"
        )
