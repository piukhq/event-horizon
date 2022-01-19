import json
import re

from typing import Dict, List, Literal, Optional

import pydantic
import wtforms
import yaml

from pydantic import BaseConfig, BaseModel, ConstrainedStr, validator

from .db.models import metadata

REQUIRED_POLARIS_JOIN_FIELDS = ["first_name", "last_name", "email"]


def _get_optional_profile_field_names() -> List[str]:  # pragma: no cover
    return [
        str(col.name)
        for col in metadata.tables["account_holder_profile"].c
        if not (col.primary_key or col.foreign_keys) and str(col.name) not in REQUIRED_POLARIS_JOIN_FIELDS
    ]


def validate_retailer_config(form: wtforms.Form, field: wtforms.Field) -> None:
    class FieldOptionsConfig(BaseConfig):
        extra = pydantic.Extra.forbid

    class FieldOptions(BaseModel):
        required: bool
        label: Optional[str] = None

        Config = FieldOptionsConfig

    def ensure_required_true(options: FieldOptions) -> FieldOptions:
        if not options.required:
            raise ValueError("'required' must be true")
        return options

    try:
        form_data = yaml.safe_load(field.data)
    except yaml.YAMLError:  # pragma: no cover
        form_data = None

    if not isinstance(form_data, dict):
        raise wtforms.ValidationError("The submitted YAML is not valid")

    required_fields = REQUIRED_POLARIS_JOIN_FIELDS + [
        field for field in _get_optional_profile_field_names() if field in form_data
    ]

    RetailerConfigModel = pydantic.create_model(
        "RetailerConfigModel",
        **{field: (FieldOptions, ...) for field in required_fields},  # type: ignore
        __config__=FieldOptionsConfig,
        __validators__={
            f"{field}_validator": validator(field, allow_reuse=True)(ensure_required_true)
            for field in REQUIRED_POLARIS_JOIN_FIELDS
        },
    )

    try:
        RetailerConfigModel(**form_data)
    except pydantic.ValidationError as ex:
        raise wtforms.ValidationError(
            ", ".join([f"{' -> '.join(err.get('loc'))}: {err.get('msg')}" for err in json.loads(ex.json())])
        )


def validate_marketing_config(form: wtforms.Form, field: wtforms.Field) -> None:

    if field.data == "":
        return

    class LabelVal(ConstrainedStr):
        strict = True
        strip_whitespace = True
        min_length = 2

    class KeyNameVal(LabelVal):
        to_lower = True

    class FieldOptions(BaseModel):
        type: Literal["boolean", "integer", "float", "string", "string_list", "date", "datetime"]
        label: LabelVal

        extra = pydantic.Extra.forbid

    class MarketingPreferenceConfigVal(BaseModel):
        __root__: Dict[KeyNameVal, FieldOptions]

    try:
        form_data = yaml.safe_load(field.data)
    except yaml.YAMLError:  # pragma: no cover
        form_data = None

    if not isinstance(form_data, dict):
        raise wtforms.ValidationError("The submitted YAML is not valid")

    try:
        validated_data = MarketingPreferenceConfigVal(__root__=form_data)
    except pydantic.ValidationError as ex:
        formatted_errors = []
        for err in json.loads(ex.json()):
            loc = err.get("loc")[1:]
            if loc[0] == "__key__":
                loc[0] = "'key'"

            formatted_errors.append(f"{' -> '.join(loc)}: {err.get('msg')}")

        raise wtforms.ValidationError(", ".join(formatted_errors))
    else:
        field.data = yaml.dump(validated_data.dict(exclude_unset=True)["__root__"], sort_keys=True)


def validate_account_number_prefix(form: wtforms.Form, field: wtforms.Field) -> None:
    required = re.compile(r"^[a-zA-Z]{2,4}$")
    if not bool(required.match(field.data)):
        raise wtforms.ValidationError("Account number prefix needs to be 2-4 alpha characters")

    field.data = field.data.upper()
