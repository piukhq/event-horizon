import json

from typing import List, Optional

import pydantic
import wtforms
import yaml

from pydantic import BaseConfig, BaseModel, validator

from app.polaris.db.models import metadata

REQUIRED_POLARIS_JOIN_FIELDS = ["first_name", "last_name", "email"]


def _get_optional_profile_field_names() -> List[str]:
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
    except yaml.YAMLError:
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
