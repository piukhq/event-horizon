import wtforms

from sqlalchemy import func
from sqlalchemy.future import select
from sqlalchemy.orm.exc import NoResultFound

from app.vela.db import db_session
from app.vela.db.models import Campaign, EarnRule


def _count_earn_rules(campaign_id: int, *, has_inc_value: bool) -> int:
    stmt = select(func.count()).select_from(EarnRule).join(Campaign).where(Campaign.id == campaign_id)
    if has_inc_value:
        stmt = stmt.where(EarnRule.increment.isnot(None))
    else:
        stmt = stmt.where(EarnRule.increment.is_(None))
    return db_session.execute(stmt).scalar()


def validate_campaign_earn_inc_is_tx_value(form: wtforms.Form, field: wtforms.Field) -> None:
    if form._obj:
        if field.data is True and _count_earn_rules(form._obj.id, has_inc_value=True):
            raise wtforms.ValidationError("This field cannot be changed as there are earn rules with increment values")
        elif field.data is False and _count_earn_rules(form._obj.id, has_inc_value=False):
            raise wtforms.ValidationError("This field cannot be changed as there are earn rules with null increments")


def validate_earn_rule_increment(form: wtforms.Form, field: wtforms.Field) -> None:
    if not (form.campaign.data.earn_inc_is_tx_value or field.data is not None):
        raise wtforms.validators.StopValidation(
            "The campaign requires that this field is populated due to campaign.earn_inc_is_tx_value setting"
        )
    elif form.campaign.data.earn_inc_is_tx_value and field.data:
        raise wtforms.ValidationError(
            "The campaign requires that this field is not populated due to campaign.earn_inc_is_tx_value setting"
        )


def validate_reward_rule_allocation_window(form: wtforms.Form, field: wtforms.Field) -> None:
    if form.campaign.data.earn_inc_is_tx_value is False and field.data != 0:
        raise wtforms.ValidationError(
            "The campaign requires that this field is set to 0 due to campaign.earn_inc_is_tx_value setting"
        )


def _get_campaign_by_id(campaign_id: int) -> Campaign:  # pragma: no cover
    return db_session.execute(select(Campaign).where(Campaign.id == campaign_id)).scalars().one()


def validate_campaign_status_change(form: wtforms.Form, field: wtforms.Field) -> None:
    campaign = _get_campaign_by_id(form._obj.id)

    if (campaign.status != "ACTIVE" and field.data == "ACTIVE") and (
        len(campaign.earnrule_collection) < 1 or len(campaign.rewardrule_collection) != 1
    ):
        raise wtforms.ValidationError("To activate a campaign one reward rule and at least one earn rule are required.")


def validate_earn_rule_deletion(campaign_id: int) -> None:
    campaign = _get_campaign_by_id(campaign_id)

    if campaign.status == "ACTIVE" and len(campaign.earnrule_collection) < 2:
        raise wtforms.ValidationError("Can not delete the last earn rule of an active campaign.")


def validate_reward_rule_deletion(campaign_id: int) -> None:
    campaign = _get_campaign_by_id(campaign_id)

    if campaign.status == "ACTIVE":
        raise wtforms.ValidationError("Can not delete the reward rule of an active campaign.")


def validate_reward_rule_change(campaign_id: int) -> None:
    try:
        campaign = _get_campaign_by_id(campaign_id)
    except NoResultFound:
        return
    else:
        if campaign.status == "ACTIVE":
            raise wtforms.ValidationError("Can not edit the reward rule of an active campaign.")
