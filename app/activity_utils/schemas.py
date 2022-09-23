from pydantic import BaseModel


class CampaignDataValuesSchema(BaseModel):
    status: str
    name: str
    loyalty_type: str
    start_date: str | None
    end_date: str | None


class CampaignDataSchema(BaseModel):
    new_values: CampaignDataValuesSchema
    original_values: CampaignDataValuesSchema | None
