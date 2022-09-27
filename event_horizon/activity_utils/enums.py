from datetime import datetime, timezone
from enum import Enum

from cosmos_message_lib.schemas import utc_datetime

from event_horizon.activity_utils.schemas import CampaignDataSchema, CampaignDataValuesSchema
from event_horizon.settings import PROJECT_NAME


class ActivityType(Enum):
    CAMPAIGN_CHANGE = f"activity.{PROJECT_NAME}.campaign.change"

    @classmethod
    def get_campaign_created_activity_data(
        cls,
        *,
        retailer_slug: str,
        campaign_name: str,
        sso_username: str,
        activity_datetime: datetime,
        campaign_slug: str,
        loyalty_type: str,
        start_date: utc_datetime | None = None,
        end_date: utc_datetime | None = None,
    ) -> dict:

        payload = {
            "type": cls.CAMPAIGN_CHANGE.name,
            "datetime": datetime.now(tz=timezone.utc),
            "underlying_datetime": activity_datetime,
            "summary": f"{campaign_name} created",
            "reasons": [],
            "activity_identifier": campaign_slug,
            "user_id": sso_username,
            "associated_value": "N/A",
            "retailer": retailer_slug,
            "campaigns": [campaign_slug],
            "data": {
                "campaign": CampaignDataSchema(
                    new_values=CampaignDataValuesSchema(
                        name=campaign_name,
                        slug=campaign_slug,
                        status="draft",
                        loyalty_type=loyalty_type.title(),
                        start_date=start_date,
                        end_date=end_date,
                    )
                ).dict(exclude_unset=True),
            },
        }
        return payload
