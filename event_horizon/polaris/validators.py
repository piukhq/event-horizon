import json
import re

from typing import Literal, Type

import pydantic
import wtforms
import yaml

from pydantic import BaseConfig, BaseModel, ConstrainedStr, validator

from event_horizon.polaris.db import RetailerConfig

from .db.models import metadata

REQUIRED_POLARIS_JOIN_FIELDS = ["first_name", "last_name", "email"]


def _get_optional_profile_field_names() -> list[str]:  # pragma: no cover
    return [
        str(col.name)
        for col in metadata.tables["account_holder_profile"].c
        if not (col.primary_key or col.foreign_keys) and str(col.name) not in REQUIRED_POLARIS_JOIN_FIELDS
    ]


# pylint: disable=unused-argument
def validate_retailer_config(form: wtforms.Form, field: wtforms.Field) -> None:
    class FieldOptionsConfig(BaseConfig):
        extra = pydantic.Extra.forbid

    class FieldOptions(BaseModel):
        required: bool
        label: str | None = None

        Config = FieldOptionsConfig  # type: Type[BaseConfig]

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

    RetailerConfigModel = pydantic.create_model(  # type: ignore [call-overload]  # pylint: disable=invalid-name
        "RetailerConfigModel",
        __config__=FieldOptionsConfig,
        __validators__={
            f"{field}_validator": validator(field, allow_reuse=True)(ensure_required_true)
            for field in REQUIRED_POLARIS_JOIN_FIELDS
        },
        **{field: (FieldOptions, ...) for field in required_fields},
    )

    try:
        RetailerConfigModel(**form_data)
    except pydantic.ValidationError as ex:
        raise wtforms.ValidationError(
            ", ".join([f"{' -> '.join(err.get('loc'))}: {err.get('msg')}" for err in json.loads(ex.json())])
        )


# pylint: disable=unused-argument
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

        extra = pydantic.Extra.forbid  # type: pydantic.Extra

    class MarketingPreferenceConfigVal(BaseModel):
        __root__: dict[KeyNameVal, FieldOptions]

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


# pylint: disable=unused-argument
def validate_account_number_prefix(form: wtforms.Form, field: wtforms.Field) -> None:
    required = re.compile(r"^[a-zA-Z]{2,4}$")
    if not bool(required.match(field.data)):
        raise wtforms.ValidationError("Account number prefix needs to be 2-4 alpha characters")

    field.data = field.data.upper()


def validate_balance_lifespan_and_warning_days(
    form: wtforms.Form,
    retailer_status: str,
) -> None:
    original_warning_days = form.balance_reset_advanced_warning_days.object_data
    new_warning_days = form.balance_reset_advanced_warning_days.data
    balance_lifespan = form.balance_lifespan.data
    if retailer_status == "ACTIVE" and new_warning_days != original_warning_days != 0:
        raise wtforms.ValidationError("You cannot change this field for an active retailer")
    if balance_lifespan != 0 == new_warning_days or balance_lifespan == 0 != new_warning_days:
        raise wtforms.ValidationError(
            "You must set both the balance_lifespan with the balance_reset_advanced_warning_days"
        )
    if balance_lifespan <= new_warning_days != 0:
        raise wtforms.ValidationError("The balance_reset_advanced_warning_days must be less than the balance_lifespan")


def validate_retailer_config_new_values(form: wtforms.Form, model: "RetailerConfig") -> tuple[dict, dict]:
    new_values: dict = {}
    original_values: dict = {}

    for field in form:
        if (new_val := getattr(model, field.name)) != field.object_data:
            new_values[field.name] = new_val
            original_values[field.name] = field.object_data

    def format_from_yaml(key_name: str) -> None:
        if key_name in new_values:
            if loaded_data := yaml.safe_load(new_values[key_name]):
                new_values[key_name] = [{"key": k, **v} for k, v in loaded_data.items()]
            else:
                new_values[key_name] = [{key_name: ""}]
            if original_values[key_name]:
                original_values[key_name] = [
                    {"key": k, **v} for k, v in yaml.safe_load(original_values[key_name]).items()
                ]
            else:
                original_values[key_name] = [{key_name: ""}]

    format_from_yaml("marketing_preference_config")
    format_from_yaml("profile_config")

    return new_values, original_values
