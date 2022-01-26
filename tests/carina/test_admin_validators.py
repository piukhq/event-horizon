from unittest import mock

import pytest
import wtforms

from app.carina.validators import validate_reward_source


@pytest.fixture
def mock_form() -> mock.MagicMock:
    return mock.MagicMock(spec=wtforms.Form)


@pytest.fixture
def mock_config_field() -> mock.MagicMock:
    return mock.MagicMock(spec=wtforms.Field)


def test_validate_reward_source_correct_validity_days(
    mock_form: mock.MagicMock, mock_config_field: mock.MagicMock
) -> None:
    mock_form.data = {"validity_days": 15}
    mock_config_field.data = "PRE_LOADED"

    validate_reward_source(mock_form, mock_config_field)


def test_validate_reward_source_empty_validity_days(
    mock_form: mock.MagicMock, mock_config_field: mock.MagicMock
) -> None:
    mock_form.data = {"validity_days": None}
    mock_config_field.data = "PRE_LOADED"
    with pytest.raises(wtforms.ValidationError) as ex_info:
        validate_reward_source(mock_form, mock_config_field)

    assert ex_info.value.args[0] == "Validity Days field is required for this Fetch Type."


def test_validate_reward_source_empty_validity_days_other_type(
    mock_form: mock.MagicMock, mock_config_field: mock.MagicMock
) -> None:
    mock_form.data = {"validity_days": None}
    mock_config_field.data = "NOT_PRE_LOADED"

    validate_reward_source(mock_form, mock_config_field)
