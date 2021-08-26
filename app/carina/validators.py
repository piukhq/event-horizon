import wtforms

from wtforms.validators import ValidationError


def voucher_source_validation(form: wtforms.Form, field: wtforms.Field) -> None:
    if field.data == "PRE_LOADED" and form.data["validity_days"] is None:
        raise ValidationError("Validity Days field is required for this Fetch Type.")
