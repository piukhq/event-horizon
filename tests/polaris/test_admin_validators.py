# pylint: disable=redefined-outer-name

from dataclasses import dataclass
from typing import Generator
from unittest import mock

import pytest
import wtforms

from event_horizon.polaris.validators import (
    validate_account_number_prefix,
    validate_balance_reset_advanced_warning_days,
    validate_marketing_config,
    validate_retailer_config,
)


@pytest.fixture()
def mock_config_field() -> mock.MagicMock:
    return mock.MagicMock(spec=wtforms.Field)


@pytest.fixture(scope="module", autouse=True)
def patched_optional_profile_field_names() -> Generator:
    with mock.patch("event_horizon.polaris.validators._get_optional_profile_field_names", new=lambda: ["phone"]):
        yield


def test_validate_retailer_config_empty(mock_form: mock.MagicMock, mock_config_field: mock.MagicMock) -> None:
    mock_config_field.data = ""
    with pytest.raises(wtforms.ValidationError) as ex_info:
        validate_retailer_config(mock_form, mock_config_field)

    assert ex_info.value.args[0] == "The submitted YAML is not valid"


def test_validate_retailer_config_string(mock_form: mock.MagicMock, mock_config_field: mock.MagicMock) -> None:
    mock_config_field.data = "just-a-little-string"
    with pytest.raises(wtforms.ValidationError) as ex_info:
        validate_retailer_config(mock_form, mock_config_field)

    assert ex_info.value.args[0] == "The submitted YAML is not valid"


def test_validate_retailer_config_minimum1(mock_form: mock.MagicMock, mock_config_field: mock.MagicMock) -> None:
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


def test_validate_retailer_config_minimum2(mock_form: mock.MagicMock, mock_config_field: mock.MagicMock) -> None:
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


def test_validate_retailer_config_minimum3(mock_form: mock.MagicMock, mock_config_field: mock.MagicMock) -> None:
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


def test_validate_retailer_config_minimum4(mock_form: mock.MagicMock, mock_config_field: mock.MagicMock) -> None:
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


def test_validate_retailer_config_optional1(mock_form: mock.MagicMock, mock_config_field: mock.MagicMock) -> None:
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


def test_validate_retailer_config_optional2(mock_form: mock.MagicMock, mock_config_field: mock.MagicMock) -> None:
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


@mock.patch("event_horizon.polaris.validators._get_optional_profile_field_names", new=lambda: ["phone", "city"])
def test_validate_retailer_config_optional3(mock_form: mock.MagicMock, mock_config_field: mock.MagicMock) -> None:
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


def test_validate_account_number_prefix(mock_form: mock.MagicMock, mock_config_field: mock.MagicMock) -> None:
    mock_config_field.data = "abC"
    validate_account_number_prefix(mock_form, mock_config_field)

    assert mock_config_field.data == "ABC"


def test_validate_account_number_prefix_numbers(mock_form: mock.MagicMock, mock_config_field: mock.MagicMock) -> None:
    mock_config_field.data = "abC6"
    with pytest.raises(wtforms.ValidationError) as ex_info:
        validate_account_number_prefix(mock_form, mock_config_field)

    assert ex_info.value.args[0] == "Account number prefix needs to be 2-4 alpha characters"


def test_validate_account_number_prefix_too_short(mock_form: mock.MagicMock, mock_config_field: mock.MagicMock) -> None:
    mock_config_field.data = "a"
    with pytest.raises(wtforms.ValidationError) as ex_info:
        validate_account_number_prefix(mock_form, mock_config_field)

    assert ex_info.value.args[0] == "Account number prefix needs to be 2-4 alpha characters"


def test_validate_account_number_prefix_too_long(mock_form: mock.MagicMock, mock_config_field: mock.MagicMock) -> None:
    mock_config_field.data = "abCdE"
    with pytest.raises(wtforms.ValidationError) as ex_info:
        validate_account_number_prefix(mock_form, mock_config_field)

    assert ex_info.value.args[0] == "Account number prefix needs to be 2-4 alpha characters"


def test_validate_marketing_config_wrong_key_name(mock_form: mock.MagicMock, mock_config_field: mock.MagicMock) -> None:
    mock_config_field.data = """
m:
    type: boolean
    label: random label
"""

    with pytest.raises(wtforms.ValidationError) as ex_info:
        validate_marketing_config(mock_form, mock_config_field)

    assert ex_info.value.args[0] == "'key': ensure this value has at least 2 characters"


def test_validate_marketing_config_missing_field(mock_form: mock.MagicMock, mock_config_field: mock.MagicMock) -> None:
    mock_config_field.data = """
marketing_conf:
    label: random label
"""

    with pytest.raises(wtforms.ValidationError) as ex_info:
        validate_marketing_config(mock_form, mock_config_field)

    assert ex_info.value.args[0] == "marketing_conf -> type: field required"


def test_validate_marketing_config_wrong_type(mock_form: mock.MagicMock, mock_config_field: mock.MagicMock) -> None:
    mock_config_field.data = """
marketing_conf:
    type: cat
    label: random label
"""

    with pytest.raises(wtforms.ValidationError) as ex_info:
        validate_marketing_config(mock_form, mock_config_field)

    assert (
        ex_info.value.args[0] == "marketing_conf -> type: "
        "unexpected value; permitted: 'boolean', 'integer', 'float', 'string', 'string_list', 'date', 'datetime'"
    )


def test_validate_marketing_config_wrong_label(mock_form: mock.MagicMock, mock_config_field: mock.MagicMock) -> None:
    mock_config_field.data = """
marketing_conf:
    type: boolean
    label: r
"""

    with pytest.raises(wtforms.ValidationError) as ex_info:
        validate_marketing_config(mock_form, mock_config_field)

    assert ex_info.value.args[0] == "marketing_conf -> label: ensure this value has at least 2 characters"


def test_validate_marketing_config_invalid_yaml(mock_form: mock.MagicMock, mock_config_field: mock.MagicMock) -> None:
    mock_config_field.data = """
marketing_conf:
    boolean
    random label
"""

    with pytest.raises(wtforms.ValidationError) as ex_info:
        validate_marketing_config(mock_form, mock_config_field)

    assert ex_info.value.args[0] == "marketing_conf: value is not a valid dict"

    mock_config_field.data = """
marketing_conf
boolean
random label
"""

    with pytest.raises(wtforms.ValidationError) as ex_info:
        validate_marketing_config(mock_form, mock_config_field)

    assert ex_info.value.args[0] == "The submitted YAML is not valid"


def test_validate_marketing_config_valid_values(mock_form: mock.MagicMock, mock_config_field: mock.MagicMock) -> None:
    mock_config_field.data = """
Marketing_conf :
    type: boolean
    label: random label
"""

    validate_marketing_config(mock_form, mock_config_field)
    # test strip whitespace, order keys, normalise key_name
    assert mock_config_field.data == "marketing_conf:\n  label: random label\n  type: boolean\n"

    mock_config_field.data = ""

    validate_marketing_config(mock_form, mock_config_field)
    assert mock_config_field.data == ""


@dataclass
class SetupData:
    original_warning_days: int
    new_warning_days: int
    status: str
    balance_lifespan: int


@dataclass
class ExpectationData:
    response: str | None


test_data = [
    [
        "balance_reset_advanced_warning_days more than balance_lifespan",
        SetupData(
            original_warning_days=0,
            new_warning_days=30,
            status="TEST",
            balance_lifespan=20,
        ),
        ExpectationData(response="The balance_reset_advanced_warning_days must be less than the balance_lifespan"),
    ],
    [
        "balance_reset_advanced_warning_days are manditory if the balance_lifespan is set",
        SetupData(
            original_warning_days=0,
            new_warning_days=0,
            status="TEST",
            balance_lifespan=20,
        ),
        ExpectationData(response="You must set both the balance_lifespan with the balance_reset_advanced_warning_days"),
    ],
    [
        "able to update the balance_reset_advanced_warning_days for a retailer >0",
        SetupData(
            original_warning_days=0,
            new_warning_days=7,
            status="ACTIVE",
            balance_lifespan=30,
        ),
        ExpectationData(response=None),
    ],
    [
        "not able to update the balance_reset_advanced_warning_days for an active retailer",
        SetupData(
            original_warning_days=7,
            new_warning_days=10,
            status="ACTIVE",
            balance_lifespan=30,
        ),
        ExpectationData(response="You cannot change this field for an active retailer"),
    ],
    [
        "not able to set a balance_lifespan without a balance_reset_advanced_warning_days for ACTIVE retailers",
        SetupData(
            original_warning_days=0,
            new_warning_days=0,
            status="ACTIVE",
            balance_lifespan=30,
        ),
        ExpectationData(
            response="You must set both the balance_lifespan with the balance_reset_advanced_warning_days "
            "for active retailers"
        ),
    ],
    [
        "able to set a balance_lifespan without a balance_reset_advanced_warning_days for TEST retailers",
        SetupData(
            original_warning_days=0,
            new_warning_days=0,
            status="TEST",
            balance_lifespan=30,
        ),
        ExpectationData(response=None),
    ],
    [
        "not able to have balance_reset_advanced_warning_days without a balance_lifespan",
        SetupData(
            original_warning_days=7,
            new_warning_days=7,
            status="TEST",
            balance_lifespan=0,
        ),
        ExpectationData(response="The balance_reset_advanced_warning_days must be less than the balance_lifespan"),
    ],
]


@pytest.mark.parametrize(
    "_description,setup_data,expectation_data",
    test_data,
    ids=[f"{i[0]}" for i in test_data],
)
def test_validate_balance_reset_advanced_warning_days(
    _description: str,
    setup_data: SetupData,
    expectation_data: ExpectationData,
) -> None:
    mock_form: wtforms.Form = {
        "balance_reset_advanced_warning_days": {
            "data": setup_data.new_warning_days,
            "object_data": setup_data.original_warning_days,
        },
        "balance_lifespan": {"data": setup_data.balance_lifespan},
    }
    retailer_status = setup_data.status
    try:
        validate_balance_reset_advanced_warning_days(mock_form, retailer_status)
    except Exception as ex:
        assert ex.args[0] == expectation_data.response
