from decimal import Decimal
from typing import Literal

from cosmos_message_lib.schemas import ActivitySchema, utc_datetime
from pydantic import BaseModel, NonNegativeInt, validator


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
    max_amount: int | None


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
    original_values: _EarnRuleDeletedValuesSchema


class EarnRuleDeletedActivitySchema(BaseModel):
    earn_rule: _EarnRuleDeletedDataSchema


class _RewardRuleCreatedValuesSchema(BaseModel):
    reward_goal: int
    refund_window: int
    reward_slug: str


class _RewardRuleCreatedDataSchema(BaseModel):
    new_values: _RewardRuleCreatedValuesSchema


class RewardRuleCreatedActivitySchema(BaseModel):
    reward_rule: _RewardRuleCreatedDataSchema


class _BalanceChangeActivityDataSchema(BaseModel):
    loyalty_type: Literal["STAMPS", "ACCUMULATOR"]
    new_balance: NonNegativeInt
    original_balance: NonNegativeInt


class BalanceChangeWholeActivitySchema(ActivitySchema):
    """
    This will be used to send bulk messages we will use the ActivitySchema on message creation
    to skip pre send validation
    """

    data: _BalanceChangeActivityDataSchema


class CampaignMigrationActivitySchema(BaseModel):
    ended_campaign: str
    activated_campaign: str
    balance_conversion_rate: int
    qualify_threshold: int
    pending_rewards: str

    @validator("balance_conversion_rate", "qualify_threshold", pre=False, always=True)
    @classmethod
    def convert_to_percentage_string(cls, v: int) -> str:
        return f"{v}%"

    @validator("pending_rewards", pre=False, always=True)
    @classmethod
    def convert_to_lower(cls, v: str) -> str:
        return v.lower()
