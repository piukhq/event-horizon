from datetime import datetime, timezone
from decimal import Decimal
from random import randint
from unittest import mock

import pytest
import wtforms

from event_horizon.vela.validators import (
    ACCUMULATOR,
    STAMPS,
    validate_campaign_end_date_change,
    validate_campaign_loyalty_type,
    validate_campaign_slug_update,
    validate_campaign_start_date_change,
    validate_campaign_status_change,
    validate_earn_rule_deletion,
    validate_earn_rule_increment,
    validate_increment_multiplier,
    validate_retailer_update,
    validate_reward_cap_for_loyalty_type,
    validate_reward_rule_allocation_window,
    validate_reward_rule_change,
    validate_reward_rule_deletion,
)


def test_validate_earn_rule_increment__accumulator__inc_has_val(
    mock_form: mock.MagicMock, mock_field: mock.MagicMock
) -> None:
    mock_form.campaign = mock.Mock(data=mock.Mock(loyalty_type=ACCUMULATOR))
    mock_field.data = 10

    with pytest.raises(wtforms.ValidationError) as ex_info:
        validate_earn_rule_increment(mock_form, mock_field)
    assert (
        ex_info.value.args[0]
        == "The campaign requires that this field is not populated due to campaign.loyalty_type setting"
    )


def test_validate_increment_multiplier__stamp__inc_has_decimal(
    mock_form: mock.MagicMock, mock_field: mock.MagicMock
) -> None:
    mock_form.campaign = mock.Mock(data=mock.Mock(loyalty_type=STAMPS))
    mock_field.data = Decimal("1.25")

    with pytest.raises(wtforms.ValidationError) as ex_info:
        validate_increment_multiplier(mock_form, mock_field)
    assert ex_info.value.args[0] == "All stamp campaigns must have an integer for this field."


def test_validate_increment_multiplier__stamp__inc_has_float(
    mock_form: mock.MagicMock, mock_field: mock.MagicMock
) -> None:
    """
    It's possible "numeric" types can be floats if using the asdecimal=False flag.
    This test is to cover the unlikely case that we alter the increment_multiplier numeric
    model field to asdecimal=False.
    """
    mock_form.campaign = mock.Mock(data=mock.Mock(loyalty_type=STAMPS))
    mock_field.data = 1.25

    with pytest.raises(wtforms.ValidationError) as ex_info:
        validate_increment_multiplier(mock_form, mock_field)
    assert ex_info.value.args[0] == "All stamp campaigns must have an integer for this field."


def test_validate_increment_multiplier__stamp__inc_has_no_decimal(
    mock_form: mock.MagicMock, mock_field: mock.MagicMock
) -> None:
    mock_form.campaign = mock.Mock(data=mock.Mock(loyalty_type=STAMPS))
    mock_field.data = Decimal(1)

    try:
        validate_increment_multiplier(mock_form, mock_field)
    except Exception:
        pytest.fail()


def test_validate_increment_multiplier__accumulator__inc_has_decimal(
    mock_form: mock.MagicMock, mock_field: mock.MagicMock
) -> None:
    mock_form.campaign = mock.Mock(data=mock.Mock(loyalty_type=ACCUMULATOR))
    mock_field.data = Decimal("1.25")

    try:
        validate_increment_multiplier(mock_form, mock_field)
    except Exception:
        pytest.fail()


def test_validate_earn_rule_increment__accumulator__inc_has_blank_val(
    mock_form: mock.MagicMock, mock_field: mock.MagicMock
) -> None:
    mock_form.campaign = mock.Mock(data=mock.Mock(loyalty_type=ACCUMULATOR))
    mock_field.data = None
    try:
        validate_earn_rule_increment(mock_form, mock_field)
    except Exception:
        pytest.fail()


def test_validate_earn_rule_increment__stamps__inc_has_val(
    mock_form: mock.MagicMock, mock_field: mock.MagicMock
) -> None:
    mock_form.campaign = mock.Mock(data=mock.Mock(loyalty_type=STAMPS))
    for val in (100, 200, 300, 500, 1000, 1200, 10000):
        mock_field.data = val

        try:
            validate_earn_rule_increment(mock_form, mock_field)
        except Exception:
            pytest.fail()

    for val in (1, 2, 10, 50, 101, 250, 399, 560, 1050, 1210, 10042):
        mock_field.data = val

        with pytest.raises(wtforms.validators.StopValidation) as ex_info:
            validate_earn_rule_increment(mock_form, mock_field)
        assert ex_info.value.args[0] == "This field must be a multiple of 100"


def test_validate_earn_rule_increment__stamps__inc_has_blank_val(
    mock_form: mock.MagicMock, mock_field: mock.MagicMock
) -> None:
    mock_form.campaign = mock.Mock(data=mock.Mock(loyalty_type=STAMPS))
    mock_field.data = None
    with pytest.raises(wtforms.validators.StopValidation) as ex_info:
        validate_earn_rule_increment(mock_form, mock_field)
    assert (
        ex_info.value.args[0]
        == "The campaign requires that this field is populated due to campaign.loyalty_type setting"
    )


@mock.patch("event_horizon.vela.validators._count_earn_rules")
def test_validate_campaign_loyalty_type__new_object(
    mock__count_earn_rules: mock.MagicMock, mock_form: mock.MagicMock, mock_field: mock.MagicMock
) -> None:
    mock_form._obj = None
    try:
        validate_campaign_loyalty_type(mock_form, mock_field)
    except Exception:
        pytest.fail()


@mock.patch("event_horizon.vela.validators._count_earn_rules")
def test_validate_campaign_loyalty_type__accumulator__earn_rules_with_inc_val(
    mock__count_earn_rules: mock.MagicMock, mock_form: mock.MagicMock, mock_field: mock.MagicMock
) -> None:
    mock_form._obj = mock.Mock(id=1)
    mock_field.data = ACCUMULATOR
    mock__count_earn_rules.return_value = 10
    with pytest.raises(wtforms.ValidationError) as ex_info:
        validate_campaign_loyalty_type(mock_form, mock_field)
    assert ex_info.value.args[0] == "This field cannot be changed as there are earn rules with increment values"
    mock__count_earn_rules.assert_called_with(1, has_inc_value=True)


@mock.patch("event_horizon.vela.validators._count_earn_rules")
def test_validate_campaign_loyalty_type__stamps__earn_rules_with_inc_val(
    mock__count_earn_rules: mock.MagicMock, mock_form: mock.MagicMock, mock_field: mock.MagicMock
) -> None:
    mock_form._obj = mock.Mock(id=1)
    mock_field.data = STAMPS
    mock__count_earn_rules.return_value = 10
    with pytest.raises(wtforms.ValidationError) as ex_info:
        validate_campaign_loyalty_type(mock_form, mock_field)
    assert ex_info.value.args[0] == "This field cannot be changed as there are earn rules with null increments"
    mock__count_earn_rules.assert_called_with(1, has_inc_value=False)


@mock.patch("event_horizon.vela.validators._count_earn_rules")
def test_validate_campaign_loyalty_type__stamps__zero_earn_rules_with_inc_val(
    mock__count_earn_rules: mock.MagicMock, mock_form: mock.MagicMock, mock_field: mock.MagicMock
) -> None:
    mock_form._obj = mock.Mock(id=1)
    mock_field.data = STAMPS
    mock__count_earn_rules.return_value = 0
    try:
        validate_campaign_loyalty_type(mock_form, mock_field)
    except Exception:
        pytest.fail()
    mock__count_earn_rules.assert_called_with(1, has_inc_value=False)


@mock.patch("event_horizon.vela.validators._count_earn_rules")
def test_validate_campaign_loyalty_type__accumulator__zero_earn_rules_with_inc_val(
    mock__count_earn_rules: mock.MagicMock, mock_form: mock.MagicMock, mock_field: mock.MagicMock
) -> None:
    mock_form._obj = mock.Mock(id=1)
    mock_field.data = ACCUMULATOR
    mock__count_earn_rules.return_value = 0
    try:
        validate_campaign_loyalty_type(mock_form, mock_field)
    except Exception:
        pytest.fail()
    mock__count_earn_rules.assert_called_with(1, has_inc_value=True)


@mock.patch("event_horizon.vela.validators._get_campaign_by_id")
def test_validate_campaign_status_change_all_good(
    mock_campaign: mock.MagicMock, mock_form: mock.MagicMock, mock_field: mock.MagicMock
) -> None:
    mock_form._obj = mock.Mock(id=1)
    mock_field.data = "ACTIVE"
    mock_campaign.return_value = mock.MagicMock(status="DRAFT", earnrule_collection=[1], rewardrule_collection=[1])

    validate_campaign_status_change(mock_form, mock_field)


@mock.patch("event_horizon.vela.validators._get_campaign_by_id")
def test_validate_campaign_status_change_no_rules(
    mock_campaign: mock.MagicMock, mock_form: mock.MagicMock, mock_field: mock.MagicMock
) -> None:
    mock_form._obj = mock.Mock(id=1)
    mock_field.data = "ACTIVE"
    mock_campaign.return_value = mock.MagicMock(status="DRAFT", earnrule_collection=[], rewardrule_collection=[])

    with pytest.raises(wtforms.ValidationError):
        validate_campaign_status_change(mock_form, mock_field)


@mock.patch("event_horizon.vela.validators._get_campaign_by_id")
def test_validate_campaign_status_change_no_earn_rules(
    mock_campaign: mock.MagicMock, mock_form: mock.MagicMock, mock_field: mock.MagicMock
) -> None:
    mock_form._obj = mock.Mock(id=1)
    mock_field.data = "ACTIVE"
    mock_campaign.return_value = mock.MagicMock(status="DRAFT", earnrule_collection=[], rewardrule_collection=[1])

    with pytest.raises(wtforms.ValidationError):
        validate_campaign_status_change(mock_form, mock_field)


@mock.patch("event_horizon.vela.validators._get_campaign_by_id")
def test_validate_campaign_status_change_no_reward_rule(
    mock_campaign: mock.MagicMock, mock_form: mock.MagicMock, mock_field: mock.MagicMock
) -> None:
    mock_form._obj = mock.Mock(id=1)
    mock_field.data = "ACTIVE"
    mock_campaign.return_value = mock.MagicMock(status="DRAFT", earnrule_collection=[1], rewardrule_collection=[])

    with pytest.raises(wtforms.ValidationError):
        validate_campaign_status_change(mock_form, mock_field)


@mock.patch("event_horizon.vela.validators._get_campaign_by_id")
def test_validate_campaign_status_change_already_active(
    mock_campaign: mock.MagicMock, mock_form: mock.MagicMock, mock_field: mock.MagicMock
) -> None:
    mock_form._obj = mock.Mock(id=1)
    mock_field.data = "ACTIVE"
    mock_campaign.return_value = mock.MagicMock(status="ACTIVE", earnrule_collection=[], rewardrule_collection=[])

    validate_campaign_status_change(mock_form, mock_field)


@mock.patch("event_horizon.vela.validators._get_campaign_by_id")
def test_validate_earn_rule_deletion_active_campaign_not_last_rule(mock_campaign: mock.MagicMock) -> None:
    mock_campaign.return_value = mock.MagicMock(status="ACTIVE", earnrule_collection=[1, 2], rewardrule_collection=[])

    validate_earn_rule_deletion(1)


@mock.patch("event_horizon.vela.validators._get_campaign_by_id")
def test_validate_earn_rule_deletion_active_campaign_last_rule(mock_campaign: mock.MagicMock) -> None:
    mock_campaign.return_value = mock.MagicMock(status="ACTIVE", earnrule_collection=[1], rewardrule_collection=[])

    with pytest.raises(wtforms.ValidationError):
        validate_earn_rule_deletion(1)


@mock.patch("event_horizon.vela.validators._get_campaign_by_id")
def test_validate_earn_rule_deletion_non_active_campaign(mock_campaign: mock.MagicMock) -> None:
    mock_campaign.return_value = mock.MagicMock(status="DRAFT", earnrule_collection=[1], rewardrule_collection=[])

    validate_earn_rule_deletion(1)


@mock.patch("event_horizon.vela.validators._get_campaign_by_id")
def test_validate_reward_rule_deletion_non_active_campaign(mock_campaign: mock.MagicMock) -> None:
    mock_campaign.return_value = mock.MagicMock(status="DRAFT", earnrule_collection=[], rewardrule_collection=[1])

    validate_reward_rule_deletion(1)


@mock.patch("event_horizon.vela.validators._get_campaign_by_id")
def test_validate_reward_rule_deletion_active_campaign(mock_campaign: mock.MagicMock) -> None:
    mock_campaign.return_value = mock.MagicMock(status="ACTIVE", earnrule_collection=[], rewardrule_collection=[1])

    with pytest.raises(wtforms.ValidationError):
        validate_reward_rule_deletion(1)


def test_validate_reward_rule_change_non_active_campaign() -> None:
    mock_campaign = mock.MagicMock(status="DRAFT", earnrule_collection=[], rewardrule_collection=[1])

    validate_reward_rule_change(campaign=mock_campaign, is_created=False)


def test_validate_reward_rule_change_active_campaign() -> None:
    mock_campaign = mock.MagicMock(status="ACTIVE", earnrule_collection=[], rewardrule_collection=[1])

    with pytest.raises(wtforms.ValidationError):
        validate_reward_rule_change(campaign=mock_campaign, is_created=False)


def test_validate_reward_rule_change_created_campaign_has_no_rewardrules() -> None:
    mock_campaign = mock.MagicMock(status="ACTIVE", earnrule_collection=[], rewardrule_collection=[1])

    validate_reward_rule_change(campaign=mock_campaign, is_created=True)


def test_validate_reward_rule_change_created_campaign_has_rewardrules() -> None:
    mock_campaign = mock.MagicMock(status="ACTIVE", earnrule_collection=[], rewardrule_collection=[1, 2])

    with pytest.raises(wtforms.ValidationError):
        validate_reward_rule_change(campaign=mock_campaign, is_created=True)


def test_validate_reward_rule_allocation_window_ok(mock_form: mock.MagicMock, mock_field: mock.MagicMock) -> None:
    mock_form.campaign = mock.Mock(data=mock.Mock(loyalty_type=ACCUMULATOR))
    mock_field.data = 12
    try:
        validate_reward_rule_allocation_window(mock_form, mock_field)
    except Exception:
        pytest.fail()

    mock_form.campaign = mock.Mock(data=mock.Mock(loyalty_type=STAMPS))
    mock_field.data = 0
    try:
        validate_reward_rule_allocation_window(mock_form, mock_field)
    except Exception:
        pytest.fail()


def test_validate_reward_rule_allocation_window_fail(mock_form: mock.MagicMock, mock_field: mock.MagicMock) -> None:
    mock_form.campaign = mock.Mock(data=mock.Mock(loyalty_type=STAMPS))
    mock_field.data = 1
    with pytest.raises(wtforms.ValidationError):
        validate_reward_rule_allocation_window(mock_form, mock_field)


def test_validate_campaign_end_date_change_ok() -> None:
    start_date = datetime.now(tz=timezone.utc)

    validate_campaign_end_date_change(
        old_end_date=start_date.replace(start_date.year + 1),
        new_end_date=start_date.replace(start_date.year + 2),
        status="DRAFT",
        start_date=start_date,
    )


def test_validate_campaign_end_date_change_currently_empty_field() -> None:
    start_date = datetime.now(tz=timezone.utc)

    validate_campaign_end_date_change(
        old_end_date=None,
        new_end_date=start_date.replace(start_date.year + 2),
        status="DRAFT",
        start_date=start_date,
    )


def test_validate_campaign_end_date_change_with_empty_field() -> None:
    start_date = datetime.now(tz=timezone.utc)

    validate_campaign_end_date_change(
        old_end_date=start_date.replace(start_date.year + 2),
        new_end_date=None,
        status="DRAFT",
        start_date=start_date,
    )


def test_validate_campaign_end_date_change_with_empty_start_date() -> None:
    fake_now = datetime.now(tz=timezone.utc)

    validate_campaign_end_date_change(
        old_end_date=fake_now,
        new_end_date=fake_now.replace(fake_now.year + 1),
        status="DRAFT",
        start_date=None,
    )


def test_validate_campaign_end_date_change_bad_status() -> None:
    fake_now = datetime.now(tz=timezone.utc)

    with pytest.raises(wtforms.ValidationError) as ex_info:
        validate_campaign_end_date_change(
            old_end_date=fake_now.replace(fake_now.year + 1),
            new_end_date=fake_now,
            status="CANCELLED",
            start_date=fake_now,
        )
    assert (
        ex_info.value.args[0] == "Can not amend the end date field of anything other than a draft or active campaign."
    )


def test_validate_campaign_end_date_change_bad_new_end_date() -> None:
    fake_now = datetime.now(tz=timezone.utc)

    with pytest.raises(wtforms.ValidationError) as ex_info:
        validate_campaign_end_date_change(
            old_end_date=fake_now.replace(fake_now.year + 1),
            new_end_date=fake_now.replace(fake_now.year - 1),
            status="DRAFT",
            start_date=fake_now,
        )
    assert ex_info.value.args[0] == "Can not set end date to be earlier than start date."


def test_validate_campaign_start_date_change_ok() -> None:
    fake_now = datetime.now(tz=timezone.utc)

    validate_campaign_start_date_change(
        old_start_date=fake_now.replace(fake_now.year - 1),
        new_start_date=fake_now,
        status="DRAFT",
    )


def test_validate_campaign_start_date_change_empty_field() -> None:
    validate_campaign_start_date_change(
        old_start_date=datetime.now(tz=timezone.utc),
        new_start_date=None,
        status="DRAFT",
    )


def test_validate_campaign_start_date_change_bad_status() -> None:
    fake_now = datetime.now(tz=timezone.utc)

    with pytest.raises(wtforms.ValidationError) as ex_info:
        validate_campaign_start_date_change(
            old_start_date=fake_now.replace(fake_now.year - 1),
            new_start_date=fake_now,
            status="ACTIVE",
        )
    assert ex_info.value.args[0] == "Can not amend the start date field of anything other than a draft campaign."


def test_validate_active_campaign_earlier_end_date() -> None:
    fake_now = datetime.now(tz=timezone.utc)

    with pytest.raises(wtforms.ValidationError) as ex_info:
        validate_campaign_end_date_change(
            old_end_date=fake_now.replace(fake_now.year + 2),
            new_end_date=fake_now.replace(fake_now.year + 1),
            start_date=fake_now,
            status="ACTIVE",
        )
    assert ex_info.value.args[0] == "Active campaign end dates cannot be brought forward, they can only be extended."


def test_validate_active_campaign_extend_end_date() -> None:
    fake_now = datetime.now(tz=timezone.utc)
    validate_campaign_end_date_change(
        old_end_date=fake_now.replace(fake_now.year + 1),
        new_end_date=fake_now.replace(fake_now.year + 2),
        start_date=fake_now,
        status="ACTIVE",
    )


def test_validate_draft_campaign_extend_end_date() -> None:
    fake_now = datetime.now(tz=timezone.utc)
    validate_campaign_end_date_change(
        old_end_date=fake_now.replace(fake_now.year + 1),
        new_end_date=fake_now.replace(fake_now.year + 2),
        start_date=fake_now,
        status="DRAFT",
    )


def test_validate_draft_campaign_earlier_end_date() -> None:
    fake_now = datetime.now(tz=timezone.utc)

    validate_campaign_end_date_change(
        old_end_date=fake_now.replace(fake_now.year + 2),
        new_end_date=fake_now.replace(fake_now.year + 1),
        start_date=fake_now,
        status="DRAFT",
    )


def test_validate_retailer_update_non_draft_campaign() -> None:
    with pytest.raises(wtforms.ValidationError):
        validate_retailer_update(old_retailer="old-retailer", new_retailer="new-retailer", campaign_status="ACTIVE")


def test_validate_retailer_update_draft_campaign() -> None:
    validate_retailer_update(old_retailer="old-retailer", new_retailer="new-retailer", campaign_status="DRAFT")


def test_validate_campaign_slug_update_non_draft_campaign() -> None:
    with pytest.raises(wtforms.ValidationError):
        validate_campaign_slug_update(
            old_campaign_slug="old-campaign-slug", new_campaign_slug="new-campaign-slug", campaign_status="ACTIVE"
        )


def test_validate_campaign_slug_update_draft_campaign() -> None:
    validate_campaign_slug_update(
        old_campaign_slug="old-campaign-slug", new_campaign_slug="new-campaign-slug", campaign_status="DRAFT"
    )


def test_validate_reward_cap_for_loyalty_type_stamps(mock_form: mock.MagicMock, mock_field: mock.MagicMock) -> None:
    mock_form.campaign = mock.Mock(data=mock.Mock(loyalty_type=STAMPS))
    mock_field.data = randint(1, 10)
    with pytest.raises(wtforms.ValidationError):
        validate_reward_cap_for_loyalty_type(mock_form, mock_field)


def test_validate_reward_cap_for_loyalty_type_accumulator(
    mock_form: mock.MagicMock, mock_field: mock.MagicMock
) -> None:
    mock_form.campaign = mock.Mock(data=mock.Mock(loyalty_type=ACCUMULATOR))
    mock_field.data = randint(1, 10)

    validate_reward_cap_for_loyalty_type(mock_form, mock_field)
