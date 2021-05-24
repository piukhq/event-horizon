import wtforms


def validate_earn_rule_increment(form: wtforms.Form, field: wtforms.Field) -> None:
    if not (form.campaign.data.earn_inc_is_tx_value or field.data):
        raise wtforms.validators.StopValidation(
            "The campaign requires that this field is not blank due to campaign.earn_inc_is_tx_value setting"
        )
    elif form.campaign.data.earn_inc_is_tx_value and field.data:
        raise wtforms.ValidationError(
            "The campaign requires that this field is blank due to campaign.earn_inc_is_tx_value setting"
        )
