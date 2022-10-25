from decimal import Decimal

from cosmos_message_lib.schemas import utc_datetime
from pydantic import BaseModel, validator


class _CampaignUpdatedValuesSchema(BaseModel):
    status: str | None
    name: str | None
    slug: str | None
    loyalty_type: str | None
    start_date: utc_datetime | None
    end_date: utc_datetime | None

    @validator("start_date", "end_date")
    @classmethod
    def format_datetime(cls, dt: utc_datetime | None) -> str | None:
        return dt.strftime("%Y-%m-%d %H:%M:%S") if dt else None


class _CampaignUpdatedDataSchema(BaseModel):
    new_values: _CampaignUpdatedValuesSchema
    original_values: _CampaignUpdatedValuesSchema


class CampaignUpdatedActivitySchema(BaseModel):
    campaign: _CampaignUpdatedDataSchema


class _CampaignCreatedValuesSchema(_CampaignUpdatedValuesSchema):
    status: str
    name: str
    slug: str
    loyalty_type: str


class _CampaignCreatedDataSchema(BaseModel):
    new_values: _CampaignCreatedValuesSchema


class CampaignCreatedActivitySchema(BaseModel):
    campaign: _CampaignCreatedDataSchema


class _EarnRuleUpdatedValuesSchema(BaseModel):
    threshold: int | None
    increment: int | None
    increment_multiplier: Decimal | None


class _EarnRuleUpdatedDataSchema(BaseModel):
    new_values: _EarnRuleUpdatedValuesSchema
    original_values: _EarnRuleUpdatedValuesSchema


class EarnRuleUpdatedActivitySchema(BaseModel):
    earn_rule: _EarnRuleUpdatedDataSchema


class _EarnRuleCreatedValuesSchema(_EarnRuleUpdatedValuesSchema):
    threshold: int
    increment_multiplier: Decimal


class _EarnRuleCreatedDataSchema(BaseModel):
    new_values: _EarnRuleCreatedValuesSchema


class EarnRuleCreatedActivitySchema(BaseModel):
    earn_rule: _EarnRuleCreatedDataSchema


class _EarnRuleDeletedValuesSchema(_EarnRuleCreatedValuesSchema):
    pass


class _EarnRuleDeletedDataSchema(BaseModel):
    new_values: _EarnRuleDeletedValuesSchema


class EarnRuleDeletedActivitySchema(BaseModel):
    earn_rule: _EarnRuleDeletedDataSchema
