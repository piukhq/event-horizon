from unittest import mock

import pytest
import wtforms
from wtforms.validators import StopValidation

from event_horizon.carina.validators import (
    validate_optional_yaml,
    validate_required_fields_values_yaml,
    validate_retailer_fetch_type,
)


def test_validate_retailer_fetch_type(mock_form: mock.MagicMock, mock_field: mock.MagicMock) -> None:
    pre_loaded_fetch_type = mock.Mock(name="PRE_LOADED")
    mock_form.retailer = mock.Mock(data=mock.Mock(fetch_types=[pre_loaded_fetch_type]))
    mock_field.data = pre_loaded_fetch_type

    validate_retailer_fetch_type(mock_form, mock_field)


def test_validate_retailer_fetch_type_wrong_fetch_type(mock_form: mock.MagicMock, mock_field: mock.MagicMock) -> None:
    mock_form.retailer = mock.Mock(data=mock.Mock(fetch_types=[mock.Mock(name="JIGSAW_EGIFT")]))
    mock_field.data = mock.Mock(name="PRE_LOADED")

    with pytest.raises(wtforms.ValidationError) as ex_info:
        validate_retailer_fetch_type(mock_form, mock_field)

    assert ex_info.value.args[0] == "Fetch Type not allowed for this retailer"


def test_validate_required_fields_values_ok(mock_form: mock.MagicMock, mock_field: mock.MagicMock) -> None:
    mock_form.fetchtype = mock.Mock(data=mock.Mock(required_fields="validity_days: integer"))
    mock_field.data = "validity_days: 15"

    validate_required_fields_values_yaml(mock_form, mock_field)


def test_validate_required_fields_values_ok_empty_string(mock_form: mock.MagicMock, mock_field: mock.MagicMock) -> None:
    mock_form.fetchtype = mock.Mock(data=mock.Mock(required_fields=""))
    mock_field.data = ""

    validate_required_fields_values_yaml(mock_form, mock_field)


def test_validate_required_fields_values_ok_none_value(mock_form: mock.MagicMock, mock_field: mock.MagicMock) -> None:
    mock_form.fetchtype = mock.Mock(data=mock.Mock(required_fields=None))
    mock_field.data = ""

    validate_required_fields_values_yaml(mock_form, mock_field)


def test_validate_required_fields_values_mismatched_keys(mock_form: mock.MagicMock, mock_field: mock.MagicMock) -> None:
    mock_form.fetchtype = mock.Mock(data=mock.Mock(required_fields="transaction_value: integer"))
    mock_field.data = "validity_days: 15"

    with pytest.raises(StopValidation) as ex_info:
        validate_required_fields_values_yaml(mock_form, mock_field)

    assert ex_info.value.args[0] == "transaction_value: field required, validity_days: extra fields not permitted"


def test_validate_required_fields_values_invalid_yaml(mock_form: mock.MagicMock, mock_field: mock.MagicMock) -> None:
    mock_form.fetchtype = mock.Mock(data=mock.Mock(required_fields="transaction_value: integer"))
    mock_field.data = "transaction_value_15"

    with pytest.raises(StopValidation) as ex_info:
        validate_required_fields_values_yaml(mock_form, mock_field)

    assert ex_info.value.args[0] == "The submitted YAML is not valid."


def test_validate_required_fields_values_mismatched_value(
    mock_form: mock.MagicMock, mock_field: mock.MagicMock
) -> None:
    mock_form.fetchtype = mock.Mock(data=mock.Mock(required_fields="validity_days: integer"))
    mock_field.data = "validity_days: five"

    with pytest.raises(StopValidation) as ex_info:
        validate_required_fields_values_yaml(mock_form, mock_field)

    assert ex_info.value.args[0] == "validity_days: value is not a valid integer"


def test_validate_required_fields_values_missing_field(mock_form: mock.MagicMock, mock_field: mock.MagicMock) -> None:
    mock_form.fetchtype = mock.Mock(data=mock.Mock(required_fields="validity_days: integer\nother: string"))
    mock_field.data = "validity_days: 15"

    with pytest.raises(StopValidation) as ex_info:
        validate_required_fields_values_yaml(mock_form, mock_field)

    assert ex_info.value.args[0] == "other: field required"


def test_validate_required_fields_values_mismatched_one_empty(
    mock_form: mock.MagicMock, mock_field: mock.MagicMock
) -> None:
    mock_form.fetchtype = mock.Mock(data=mock.Mock(required_fields=""))
    mock_field.data = "validity_days: 15"

    with pytest.raises(StopValidation) as ex_info:
        validate_required_fields_values_yaml(mock_form, mock_field)

    assert ex_info.value.args[0] == "'required_fields_values' must be empty for this fetch type."


def test_validate_optional_yaml_ok(mock_form: mock.MagicMock, mock_field: mock.MagicMock) -> None:
    mock_field.data = "test: yaml\ncorrect:  format"
    validate_optional_yaml(mock_form, mock_field)

    assert mock_field.data == "correct: format\ntest: yaml\n"


def test_validate_optional_yaml_none(mock_form: mock.MagicMock, mock_field: mock.MagicMock) -> None:
    mock_field.data = None
    validate_optional_yaml(mock_form, mock_field)

    assert not mock_field.data


def test_validate_optional_yaml_invalid_yaml(mock_form: mock.MagicMock, mock_field: mock.MagicMock) -> None:
    mock_field.data = "invalid yaml"

    with pytest.raises(StopValidation) as ex_info:
        validate_optional_yaml(mock_form, mock_field)

    assert ex_info.value.args[0] == "The submitted YAML is not valid."
