from datetime import datetime

import wtforms

from sqlalchemy import func
from sqlalchemy.future import select

from event_horizon.vela.db import Campaign, EarnRule, db_session

ACCUMULATOR, STAMPS = "ACCUMULATOR", "STAMPS"


def _count_earn_rules(campaign_id: int, *, has_inc_value: bool) -> int:
    stmt = select(func.count()).select_from(EarnRule).join(Campaign).where(Campaign.id == campaign_id)
    stmt = stmt.where(EarnRule.increment.isnot(None)) if has_inc_value else stmt.where(EarnRule.increment.is_(None))
    return db_session.execute(stmt).scalar()


def validate_campaign_loyalty_type(form: wtforms.Form, field: wtforms.Field) -> None:
    if form._obj:
        if field.data == ACCUMULATOR and _count_earn_rules(form._obj.id, has_inc_value=True):
            raise wtforms.ValidationError("This field cannot be changed as there are earn rules with increment values")

        if field.data == STAMPS and _count_earn_rules(form._obj.id, has_inc_value=False):
            raise wtforms.ValidationError("This field cannot be changed as there are earn rules with null increments")


def validate_earn_rule_increment(form: wtforms.Form, field: wtforms.Field) -> None:
    if form.campaign.data.loyalty_type == STAMPS:
        if field.data is None:
            raise wtforms.validators.StopValidation(
                "The campaign requires that this field is populated due to campaign.loyalty_type setting"
            )
        if field.data % 100:
            raise wtforms.validators.StopValidation("This field must be a multiple of 100")

    if form.campaign.data.loyalty_type == ACCUMULATOR and field.data is not None:
        raise wtforms.ValidationError(
            "The campaign requires that this field is not populated due to campaign.loyalty_type setting"
        )


def validate_earn_rule_max_amount(form: wtforms.Form, field: wtforms.Field) -> None:
    if form.campaign.data.loyalty_type != ACCUMULATOR and field.data != 0:
        raise wtforms.ValidationError(
            "The campaign requires that this field is set to 0 due to campaign.loyalty_type setting"
        )


def validate_reward_rule_allocation_window(form: wtforms.Form, field: wtforms.Field) -> None:
    if form.campaign.data.loyalty_type == STAMPS and field.data != 0:
        raise wtforms.ValidationError(
            "The campaign requires that this field is set to 0 due to campaign.loyalty_type setting"
        )


def _get_campaign_by_id(campaign_id: int) -> Campaign:  # pragma: no cover
    return db_session.execute(select(Campaign).where(Campaign.id == campaign_id)).scalars().one()


def validate_campaign_status_change(form: wtforms.Form, field: wtforms.Field) -> None:
    campaign = _get_campaign_by_id(form._obj.id)

    if (campaign.status != "ACTIVE" and field.data == "ACTIVE") and (
        len(campaign.earnrule_collection) < 1 or len(campaign.rewardrule_collection) != 1
    ):
        raise wtforms.ValidationError("To activate a campaign one reward rule and at least one earn rule are required.")


def validate_increment_multiplier(form: wtforms.Form, field: wtforms.Field) -> None:
    if form.campaign.data.loyalty_type == STAMPS and not str(field.data).isnumeric():
        raise wtforms.ValidationError("All stamp campaigns must have an integer for this field.")


def validate_campaign_start_date_change(
    old_start_date: datetime | None, new_start_date: datetime | None, status: str
) -> None:
    if old_start_date:
        old_start_date = old_start_date.replace(microsecond=0)
    if status != "DRAFT" and new_start_date != old_start_date:
        raise wtforms.ValidationError("Can not amend the start date field of anything other than a draft campaign.")


def validate_campaign_end_date_change(
    old_end_date: datetime | None, new_end_date: datetime | None, start_date: datetime | None, status: str
) -> None:
    if old_end_date:
        old_end_date = old_end_date.replace(microsecond=0)
    if status not in ("DRAFT", "ACTIVE") and new_end_date != old_end_date:
        raise wtforms.ValidationError(
            "Can not amend the end date field of anything other than a draft or active campaign."
        )

    if new_end_date and start_date:
        if new_end_date < start_date:
            raise wtforms.ValidationError("Can not set end date to be earlier than start date.")
        if old_end_date and status == "ACTIVE" and old_end_date > new_end_date:
            raise wtforms.ValidationError(
                "Active campaign end dates cannot be brought forward, they can only be extended."
            )


def validate_earn_rule_deletion(campaign_id: int) -> None:
    campaign = _get_campaign_by_id(campaign_id)

    if campaign.status == "ACTIVE" and len(campaign.earnrule_collection) < 2:
        raise wtforms.ValidationError("Can not delete the last earn rule of an active campaign.")


def validate_reward_rule_deletion(campaign_id: int) -> None:
    campaign = _get_campaign_by_id(campaign_id)

    if campaign.status == "ACTIVE":
        raise wtforms.ValidationError("Can not delete the reward rule of an active campaign.")


def validate_reward_rule_change(campaign: Campaign, is_created: bool) -> None:
    if len(campaign.rewardrule_collection) > 1 and is_created:
        raise wtforms.ValidationError("There is already a reward rule in place for this campaign.")

    if campaign.status == "ACTIVE" and campaign.retailerrewards.status != "TEST" and not is_created:
        raise wtforms.ValidationError("Can not edit the reward rule of an active campaign.")


def validate_reward_cap_for_loyalty_type(form: wtforms.Form, field: wtforms.Field) -> None:
    if form.campaign.data.loyalty_type != ACCUMULATOR and field.data is not None:
        raise wtforms.ValidationError("Reward cap can only be set for accumulator campaigns")


def validate_retailer_update(old_retailer: str, new_retailer: str, campaign_status: str) -> None:
    if old_retailer != new_retailer and campaign_status != "DRAFT":
        raise wtforms.ValidationError("Can only change retailer for a draft campaign")


def validate_campaign_slug_update(old_campaign_slug: str, new_campaign_slug: str, campaign_status: str) -> None:
    if old_campaign_slug != new_campaign_slug and campaign_status != "DRAFT":
        raise wtforms.ValidationError("Can only change campaign slug for a draft campaign")
