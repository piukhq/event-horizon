import json

from typing import List, Optional

import pydantic
import wtforms
import yaml

from pydantic import BaseConfig, BaseModel, Field, validator

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

    class FieldOptionsModel(BaseModel):
        required: bool = False
        label: Optional[str] = None

        Config = FieldOptionsConfig

    class RequiredFieldOptionsModel(FieldOptionsModel, BaseModel):
        required: bool

        @validator("required", allow_reuse=True)
        def must_be_true(cls, v: bool) -> bool:
            if not v:
                raise ValueError("'required' must be true")
            return v

    RetailerConfigModel = pydantic.create_model(
        "RetailerConfigModel",
        **{fld: (RequiredFieldOptionsModel, Field(...)) for fld in REQUIRED_POLARIS_JOIN_FIELDS},  # type: ignore
        **{fld: (FieldOptionsModel, Field(None)) for fld in _get_optional_profile_field_names()},  # type: ignore
        __config__=FieldOptionsConfig,
    )

    try:
        RetailerConfigModel(**yaml.safe_load(field.data))
    except (yaml.YAMLError, TypeError):
        raise wtforms.ValidationError("The submitted YAML is not valid")
    except pydantic.ValidationError as ex:
        raise wtforms.ValidationError(
            ", ".join([f"{' -> '.join(err.get('loc'))}: {err.get('msg')}" for err in json.loads(ex.json())])
        )
