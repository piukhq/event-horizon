import hashlib
import logging
import re

from typing import TYPE_CHECKING, Any, TypedDict

from sqlalchemy.future import select
from sqlalchemy.orm.attributes import flag_modified

from event_horizon.hubble.db.models import Activity
from event_horizon.hubble.db.session import SyncSessionMaker
from event_horizon.hubble.enums import AccountActivities

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


ACCOUNT_CREDENTIALS = (
    "email",
    "first_name",
    "last_name",
    "date_of_birth",
    "phone",
    "address_line1",
    "address_line2",
    "postcode",
    "city",
    "custom",
)


class AccountRequestActivityDataFields(TypedDict):
    value: str
    field_name: str


class AccountRequestActivityData(TypedDict):
    fields: list[AccountRequestActivityDataFields]
    channel: str
    datatime: str


def _encode_value(account_holder_uuid: str, value: Any | None) -> str:
    """
    Returns hashlib.sha224 encoded hash str of the input str account_holder_uuid

    If the value to hash isn't the account_holder_uuid, account_holder_uuid is still
    required as it is used as suffix and the combined str is hashed
    """
    if not value:
        identifier = str(account_holder_uuid)
    else:
        identifier = value + str(account_holder_uuid)

    encoded_value = hashlib.sha224((identifier).encode("utf-8")).hexdigest()
    return encoded_value


def _encode_email_in_string(account_holder_uuid: str, str_val: str) -> str:
    """
    Return the original string with an email with the email replaced with
    a hashed email + account_holder_uuid value

    i.e 'Enrolment Requested for qatest+011@bink.com' becomes
    'Enrolment Requested for 5a8612c878a17ec322d90d6ae2c26007533b4cb4699b4392d44f106d'

    Parameters:
            account_holder_uuid (str): the account holder uuid
            str_val (str): The original string containing an email

    Returns:
            hashed_str (str): Original string with hashed email
    """
    pattern = r"[\w.+-]+@[\w-]+\.[\w.-]+"
    extracted_val = re.findall(pattern, str_val)
    encoded_val = _encode_value(account_holder_uuid, extracted_val[0])
    return re.sub(pattern, encoded_val, str_val)


def _encode_field_values_in_data(
    account_holder_uuid: str, data: AccountRequestActivityData
) -> AccountRequestActivityData:
    """
    Returns the input AccountRequestActivityData with the specified
    field values hashed with _encode_value fn

    Parameters:
            account_holder_uuid (str): the account holder uuid
            data (AccountRequestActivityData): The original activity data

    Returns:
            data (AccountRequestActivityData): Original data with hashed field values
    """
    for field in data["fields"]:
        if field["field_name"] in ACCOUNT_CREDENTIALS:
            field["value"] = _encode_value(account_holder_uuid, field["value"])
    return data


def _get_all_account_activities(
    db_session: "Session", retailer_slug: str, account_holder_uuid: str, account_holder_email: str
) -> list[Activity]:
    activities_to_update = []
    for activity_type in AccountActivities:
        res = (
            db_session.execute(
                select(Activity)
                .where(Activity.retailer == retailer_slug, Activity.type == activity_type.value)
                .filter(
                    (Activity.associated_value.ilike(account_holder_email)) | (Activity.user_id == account_holder_uuid)
                )
            )
            .scalars()
            .all()
        )
        activities_to_update.append(res)
    return activities_to_update


def _anonymise_generic_account_activity(activity: Activity, account_holder_uuid: str) -> list:
    activity.user_id = _encode_value(account_holder_uuid, value=None)
    return activity.id


def _anonymise_account_request_activity(activity: Activity, account_holder_uuid: str) -> list:
    activity.summary = _encode_email_in_string(account_holder_uuid, activity.summary)
    activity.associated_value = _encode_value(account_holder_uuid, activity.associated_value)
    activity.data = _encode_field_values_in_data(account_holder_uuid, activity.data)
    flag_modified(activity, "data")
    return activity.id


def anonymise_account_activities(retailer_slug: str, account_holder_uuid: str, account_holder_email: str) -> None:
    with SyncSessionMaker() as db_session:
        activities_all_types = _get_all_account_activities(
            db_session, retailer_slug, account_holder_uuid, account_holder_email
        )
        activities_updated = []
        for activities in activities_all_types:
            for activity in activities:
                if activity.type == AccountActivities.ACCOUNT_REQUEST.value:
                    updated_activity_id = _anonymise_account_request_activity(activity, account_holder_uuid)
                else:
                    updated_activity_id = _anonymise_generic_account_activity(activity, account_holder_uuid)

                activities_updated.append(updated_activity_id)

        if activities_updated:
            try:
                db_session.commit()
                logging.info("Successfully applied updates to the following activities: %s", activities_updated)
            except Exception as ex:
                db_session.rollback()
                logging.exception(
                    "Failed to annonymise activity for account_holder_uuid: %s", account_holder_uuid, exc_info=ex
                )
        else:
            logging.info("No activities to update")
