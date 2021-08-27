import wtforms

from wtforms.validators import ValidationError


def validate_voucher_source(form: wtforms.Form, field: wtforms.Field) -> None:
    if field.data == "PRE_LOADED" and form.data["validity_days"] is None:
        raise ValidationError("Validity Days field is required for this Fetch Type.")
