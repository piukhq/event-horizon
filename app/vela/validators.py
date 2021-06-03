import wtforms

from app.vela.db import db_session
from app.vela.db.models import Campaign, EarnRule


def _count_earn_rules(campaign_id: int, *, has_inc_value: bool) -> int:
    query = db_session.query(EarnRule).filter(Campaign.id == campaign_id)
    if has_inc_value:
        return query.filter(EarnRule.increment.isnot(None)).count()
    else:
        return query.filter(EarnRule.increment.is_(None)).count()


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
