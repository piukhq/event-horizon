from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum

from cosmos_message_lib.schemas import utc_datetime

from event_horizon.activity_utils.schemas import (
    CampaignCreatedActivitySchema,
    CampaignUpdatedActivitySchema,
    EarnRuleCreatedActivitySchema,
    EarnRuleDeletedActivitySchema,
    EarnRuleUpdatedActivitySchema,
)
from event_horizon.settings import PROJECT_NAME


class ActivityType(Enum):
    CAMPAIGN_CHANGE = f"activity.{PROJECT_NAME}.campaign.change"
    EARN_RULE_CHANGE = f"activity.{PROJECT_NAME}.earn_rule.change"

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
            "data": CampaignCreatedActivitySchema(
                campaign={
                    "new_values": {
                        "name": campaign_name,
                        "slug": campaign_slug,
                        "status": "draft",
                        "loyalty_type": loyalty_type.title(),
                        "start_date": start_date,
                        "end_date": end_date,
                    }
                }
            ).dict(exclude_unset=True),
        }
        return payload

    @classmethod
    def get_campaign_updated_activity_data(
        cls,
        *,
        retailer_slug: str,
        campaign_name: str,
        sso_username: str,
        activity_datetime: datetime,
        campaign_slug: str,
        new_values: dict,
        original_values: dict,
    ) -> dict:

        payload = {
            "type": cls.CAMPAIGN_CHANGE.name,
            "datetime": datetime.now(tz=timezone.utc),
            "underlying_datetime": activity_datetime,
            "summary": f"{campaign_name} changed",
            "reasons": [],
            "activity_identifier": campaign_slug,
            "user_id": sso_username,
            "associated_value": "N/A",
            "retailer": retailer_slug,
            "campaigns": [campaign_slug],
            "data": CampaignUpdatedActivitySchema(
                campaign={
                    "new_values": new_values,
                    "original_values": original_values,
                }
            ).dict(exclude_unset=True),
        }

        return payload

    @classmethod
    def get_earn_rule_created_activity_data(
        cls,
        *,
        retailer_slug: str,
        campaign_name: str,
        sso_username: str,
        activity_datetime: datetime,
        campaign_slug: str,
        threshold: int,
        increment: int,
        increment_multiplier: Decimal,
    ) -> dict:

        payload = {
            "type": cls.EARN_RULE_CHANGE.name,
            "datetime": datetime.now(tz=timezone.utc),
            "underlying_datetime": activity_datetime,
            "summary": f"{campaign_name} Earn Rule created",
            "reasons": [],
            "activity_identifier": campaign_slug,
            "user_id": sso_username,
            "associated_value": "N/A",
            "retailer": retailer_slug,
            "campaigns": [campaign_slug],
            "data": EarnRuleCreatedActivitySchema(
                earn_rule={
                    "new_values": {
                        "threshold": threshold,
                        "increment": increment,
                        "increment_multiplier": increment_multiplier,
                    }
                }
            ).dict(exclude_unset=True),
        }
        return payload

    @classmethod
    def get_earn_rule_updated_activity_data(
        cls,
        *,
        retailer_slug: str,
        campaign_name: str,
        sso_username: str,
        activity_datetime: datetime,
        campaign_slug: str,
        new_values: dict,
        original_values: dict,
    ) -> dict:

        payload = {
            "type": cls.EARN_RULE_CHANGE.name,
            "datetime": datetime.now(tz=timezone.utc),
            "underlying_datetime": activity_datetime,
            "summary": f"{campaign_name} Earn Rule changed",
            "reasons": [],
            "activity_identifier": campaign_slug,
            "user_id": sso_username,
            "associated_value": "N/A",
            "retailer": retailer_slug,
            "campaigns": [campaign_slug],
            "data": EarnRuleUpdatedActivitySchema(
                earn_rule={
                    "new_values": new_values,
                    "original_values": original_values,
                }
            ).dict(exclude_unset=True),
        }

        return payload

    @classmethod
    def get_earn_rule_deleted_activity_data(
        cls,
        *,
        retailer_slug: str,
        campaign_name: str,
        sso_username: str,
        activity_datetime: datetime,
        campaign_slug: str,
        threshold: int,
        increment: int,
        increment_multiplier: Decimal,
    ) -> dict:

        payload = {
            "type": cls.EARN_RULE_CHANGE.name,
            "datetime": datetime.now(tz=timezone.utc),
            "underlying_datetime": activity_datetime,
            "summary": f"{campaign_name} Earn Rule removed",
            "reasons": [],
            "activity_identifier": campaign_slug,
            "user_id": sso_username,
            "associated_value": "N/A",
            "retailer": retailer_slug,
            "campaigns": [campaign_slug],
            "data": EarnRuleDeletedActivitySchema(
                earn_rule={
                    "new_values": {
                        "threshold": threshold,
                        "increment": increment,
                        "increment_multiplier": increment_multiplier,
                    }
                }
            ).dict(exclude_unset=True),
        }
        return payload
