from typing import Callable, Generator
from unittest import mock

import pytest
import wtforms


@pytest.fixture
def mock_form() -> mock.MagicMock:
    return mock.MagicMock(spec=wtforms.Form)


@pytest.fixture
def mock_config_field() -> mock.MagicMock:
    return mock.MagicMock(spec=wtforms.Field)


@pytest.fixture(scope="session")
def validate_retailer_config() -> Generator:
    with mock.patch("sqlalchemy.ext.automap.automap_base", autospec=True):
        with mock.patch("app.polaris.db.models.metadata", autospec=True) as mock_metadata:
            mock_metadata.return_value.tables = {"account_holder_profile": mock.MagicMock()}

            from app.polaris.validators import validate_retailer_config as fn

            yield fn


def test_validate_retailer_config_empty(
    validate_retailer_config: Callable, mock_form: mock.MagicMock, mock_config_field: mock.MagicMock
) -> None:
    mock_config_field.data = ""
    with pytest.raises(wtforms.ValidationError) as ex_info:
        validate_retailer_config(mock_form, mock_config_field)

    assert ex_info.value.args[0] == "The submitted YAML is not valid"


def test_validate_retailer_config_string(
    validate_retailer_config: Callable, mock_form: mock.MagicMock, mock_config_field: mock.MagicMock
) -> None:
    mock_config_field.data = "just-a-little-string"
    with pytest.raises(wtforms.ValidationError) as ex_info:
        validate_retailer_config(mock_form, mock_config_field)

    assert ex_info.value.args[0] == "The submitted YAML is not valid"


def test_validate_retailer_config_minimum1(
    validate_retailer_config: Callable, mock_form: mock.MagicMock, mock_config_field: mock.MagicMock
) -> None:
    mock_config_field.data = """
email:
    required: true
first_name:
    required: true
last_name:
    required: true
"""
    try:
        validate_retailer_config(mock_form, mock_config_field)
    except Exception as ex:
        pytest.fail(f"Unexpected exception raised ({ex})")


def test_validate_retailer_config_minimum2(
    validate_retailer_config: Callable, mock_form: mock.MagicMock, mock_config_field: mock.MagicMock
) -> None:
    mock_config_field.data = """
email:
first_name:
last_name:
"""

    with pytest.raises(wtforms.ValidationError) as ex_info:
        validate_retailer_config(mock_form, mock_config_field)

    assert (
        ex_info.value.args[0] == "first_name: none is not an allowed value, "
        "last_name: none is not an allowed value, "
        "email: none is not an allowed value"
    )


def test_validate_retailer_config_minimum3(
    validate_retailer_config: Callable, mock_form: mock.MagicMock, mock_config_field: mock.MagicMock
) -> None:
    mock_config_field.data = """
email:
    required: false
first_name:
    required: false
last_name:
    required: false
"""

    with pytest.raises(wtforms.ValidationError) as ex_info:
        validate_retailer_config(mock_form, mock_config_field)

    assert (
        ex_info.value.args[0] == "first_name: 'required' must be true, "
        "last_name: 'required' must be true, "
        "email: 'required' must be true"
    )


def test_validate_retailer_config_minimum4(
    validate_retailer_config: Callable, mock_form: mock.MagicMock, mock_config_field: mock.MagicMock
) -> None:
    mock_config_field.data = """
email:
    required: true
    ooops: oh noes
first_name:
    required: true
last_name:
    required: true
"""

    with pytest.raises(wtforms.ValidationError) as ex_info:
        validate_retailer_config(mock_form, mock_config_field)

    assert ex_info.value.args[0] == "email -> ooops: extra fields not permitted"


@mock.patch("app.polaris.validators._get_optional_profile_field_names", new=lambda: ["phone"])
def test_validate_retailer_config_optional1(
    validate_retailer_config: Callable, mock_form: mock.MagicMock, mock_config_field: mock.MagicMock
) -> None:
    mock_config_field.data = """
email:
    required: true
    label: The email address
first_name:
    required: true
last_name:
    required: true
phone:
    required: false
    label: hello, is it me you're looking for?
"""
    try:
        validate_retailer_config(mock_form, mock_config_field)
    except Exception as ex:
        pytest.fail(f"Unexpected exception raised ({ex})")


@mock.patch("app.polaris.validators._get_optional_profile_field_names", new=lambda: ["phone"])
def test_validate_retailer_config_optional2(
    validate_retailer_config: Callable, mock_form: mock.MagicMock, mock_config_field: mock.MagicMock
) -> None:
    mock_config_field.data = """
email:
    required: true
    label: The email address
first_name:
    required: true
last_name:
    required: true
phone:
    required: false
    label: Phone
    mistake: no way
bad:
    label: oops
worse:
"""
    with pytest.raises(wtforms.ValidationError) as ex_info:
        validate_retailer_config(mock_form, mock_config_field)

    assert (
        ex_info.value.args[0] == "phone -> mistake: extra fields not permitted, "
        "bad: extra fields not permitted, "
        "worse: extra fields not permitted"
    )


@mock.patch("app.polaris.validators._get_optional_profile_field_names", new=lambda: ["phone", "city"])
def test_validate_retailer_config_optional3(
    validate_retailer_config: Callable, mock_form: mock.MagicMock, mock_config_field: mock.MagicMock
) -> None:
    mock_config_field.data = """
email:
    required: true
first_name:
    required: true
last_name:
    required: true
phone:
city:
"""
    with pytest.raises(wtforms.ValidationError) as ex_info:
        validate_retailer_config(mock_form, mock_config_field)

    assert ex_info.value.args[0] == "phone: none is not an allowed value, city: none is not an allowed value"
