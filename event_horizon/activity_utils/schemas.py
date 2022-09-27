from cosmos_message_lib.schemas import utc_datetime
from pydantic import BaseModel, validator


class CampaignDataValuesSchema(BaseModel):
    status: str
    name: str
    slug: str
    loyalty_type: str
    start_date: utc_datetime | None
    end_date: utc_datetime | None

    @validator("start_date", "end_date")
    @classmethod
    def format_datetime(cls, dt: utc_datetime | None) -> str | None:
        return dt.strftime("%Y-%m-%d %H:%M:%S") if dt else None


class CampaignDataSchema(BaseModel):
    new_values: CampaignDataValuesSchema
    original_values: CampaignDataValuesSchema | None
