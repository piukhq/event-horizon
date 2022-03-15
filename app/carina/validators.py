import json

import pydantic as pd
import wtforms
import yaml

from wtforms.validators import StopValidation

FIELD_TYPES = {
    "integer": int,
    "float": float,
    "string": str,
}
INVALID_YAML_ERROR = StopValidation("The submitted YAML is not valid.")


def validate_retailer_fetch_type(form: wtforms.Form, field: wtforms.Field) -> None:

    if field.data not in form.retailer.data.fetch_types:
        raise wtforms.ValidationError("Fetch Type not allowed for this retailer")


def _validate_required_fields_values(required_fields: dict, fields_to_check: dict) -> pd.BaseModel:
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
        return RequiredFieldsValuesModel(**fields_to_check)
    except pd.ValidationError as ex:
        raise StopValidation(
            ", ".join([f"{' -> '.join(err.get('loc'))}: {err.get('msg')}" for err in json.loads(ex.json())])
        )


def validate_required_fields_values_yaml(form: wtforms.Form, field: wtforms.Field) -> None:
    if form.fetchtype.data.required_fields in [None, ""]:
        required_fields = None
    else:
        required_fields = yaml.safe_load(form.fetchtype.data.required_fields)

    try:
        if field.data is None:
            field.data = None
        else:
            field_data = yaml.safe_load(field.data)
    except (yaml.YAMLError, AttributeError):  # pragma: no cover
        raise INVALID_YAML_ERROR

    if required_fields is None:
        if field_data == required_fields:
            field.data = ""
            return
        else:
            raise StopValidation("'required_fields_values' must be empty for this fetch type.")

    if not isinstance(field_data, dict):
        raise INVALID_YAML_ERROR

    field.data = yaml.dump(_validate_required_fields_values(required_fields, field_data).dict(), indent=2)


def validate_optional_yaml(form: wtforms.Form, field: wtforms.Field) -> None:
    try:

        if field.data in [None, ""]:
            field.data = ""
            return
        else:
            field_data = yaml.safe_load(field.data)

    except (yaml.YAMLError, AttributeError):  # pragma: no cover
        raise INVALID_YAML_ERROR

    if not isinstance(field_data, dict):
        raise INVALID_YAML_ERROR

    field.data = yaml.dump(field_data, indent=2)
