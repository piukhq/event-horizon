import json

import pydantic as pd
import wtforms
import yaml

from wtforms.validators import ValidationError

FIELD_TYPES = {
    "integer": int,
    "float": float,
    "string": str,
}


def validate_retailer_fetch_type(form: wtforms.Form, field: wtforms.Field) -> None:

    if field.data not in form.retailer.data.fetch_types:
        raise ValidationError("Fetch Type not allowed for this reatiler")


def validate_required_fields_values(form: wtforms.Form, field: wtforms.Field) -> None:

    try:
        required_fields = yaml.safe_load(form.fetchtype.data.required_fields)
    except (yaml.YAMLError, AttributeError):  # pragma: no cover
        required_fields = None

    try:
        field_data = yaml.safe_load(field.data)
    except (yaml.YAMLError, AttributeError):  # pragma: no cover
        field_data = None

    if required_fields is None:
        if field_data == required_fields:
            return
        else:
            raise wtforms.ValidationError("'required_fields_values' must be empty for this fetch type.")

    if not isinstance(field_data, dict):
        raise wtforms.ValidationError("The submitted YAML is not valid")

    class Config(pd.BaseConfig):
        extra = pd.Extra.forbid
        anystr_lower = True
        anystr_strip_whitespace = True
        min_anystr_length = 2

    RequiredFieldsValuesModel = pd.create_model(  # type: ignore
        "RequiredFieldsValuesModel",
        __config__=Config,
        **{k: (FIELD_TYPES[v], ...) for k, v in required_fields.items()},
    )

    try:
        parsed = RequiredFieldsValuesModel(**field_data)
    except pd.ValidationError as ex:
        raise wtforms.ValidationError(
            ", ".join([f"{' -> '.join(err.get('loc'))}: {err.get('msg')}" for err in json.loads(ex.json())])
        )
    else:
        field.data = yaml.dump(parsed.dict(), indent=2)
