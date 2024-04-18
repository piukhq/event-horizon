from collections.abc import Generator
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import func, literal
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.future import select

from event_horizon.activity_utils.enums import ActivityType
from event_horizon.polaris.db import AccountHolder, AccountHolderCampaignBalance, AccountHolderPendingReward

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def transfer_balance(  # noqa: PLR0913
    db_session: "Session",
    *,
    retailer_slug: str,
    from_campaign_slug: str,
    to_campaign_slug: str,
    to_campaign_start_date: "datetime",
    min_balance: int,
    rate_percent: int,
    loyalty_type: str,
) -> Generator[dict, None, None]:  # pragma: no cover
    rate_multiplier = rate_percent / 100

    match loyalty_type:
        case "ACCUMULATOR":
            computed_balance = func.ceil(AccountHolderCampaignBalance.balance * rate_multiplier)
        case "STAMPS":
            computed_balance = func.ceil((AccountHolderCampaignBalance.balance * rate_multiplier) / 100) * 100
        case _:
            raise ValueError(f"Unexpected loyalty type '{loyalty_type}' received. Expected ACCUMULATOR or STAMPS.")

    insert_values_stmt = select(
        literal(to_campaign_slug).label("campaign_slug"),
        AccountHolderCampaignBalance.account_holder_id,
        computed_balance.label("balance"),
        AccountHolderCampaignBalance.reset_date,
    ).where(
        AccountHolderCampaignBalance.campaign_slug == from_campaign_slug,
        AccountHolderCampaignBalance.balance >= min_balance,
        AccountHolderCampaignBalance.balance > 0,
    )
    insert_stmt = (
        insert(AccountHolderCampaignBalance)
        .returning(
            AccountHolderCampaignBalance.account_holder_id,
            AccountHolderCampaignBalance.balance,
        )
        .from_select(insert_values_stmt.c.keys(), insert_values_stmt)
    )
    upsert_stmt = insert_stmt.on_conflict_do_update(
        index_elements=["account_holder_id", "campaign_slug"],
        set_={
            "balance": AccountHolderCampaignBalance.balance + insert_stmt.excluded.balance,
            "reset_date": insert_stmt.excluded.reset_date,
        },
    )
    updated_balances = db_session.execute(upsert_stmt).all()

    account_holder_id_map = dict(
        db_session.execute(
            select(AccountHolder.id, AccountHolder.account_holder_uuid).where(
                AccountHolder.id.in_([val[0] for val in updated_balances])
            )
        ).all()
    )

    return (
        ActivityType.get_balance_change_activity_data(
            retailer_slug=retailer_slug,
            from_campaign_slug=from_campaign_slug,
            to_campaign_slug=to_campaign_slug,
            account_holder_uuid=account_holder_id_map[ah_id],
            activity_datetime=to_campaign_start_date,
            new_balance=balance,
            loyalty_type=loyalty_type,
        )
        for ah_id, balance in updated_balances
    )


def transfer_pending_rewards(  # noqa: PLR0913
    db_session: "Session",
    *,
    retailer_slug: str,
    from_campaign_slug: str,
    to_campaign_slug: str,
    to_campaign_reward_slug: str,
    to_campaign_start_date: "datetime",
) -> Generator[dict, None, None]:  # pragma: no cover
    updated_rewards = db_session.execute(
        AccountHolderPendingReward.__table__.update()
        # NB: we might want to remove reward_slug here when we stop using it
        .values(campaign_slug=to_campaign_slug, reward_slug=to_campaign_reward_slug)
        .where(
            AccountHolderPendingReward.campaign_slug == from_campaign_slug,
            # this is needed to return the account_holder_uuid
            AccountHolderPendingReward.account_holder_id == AccountHolder.id,
        )
        .returning(AccountHolderPendingReward.pending_reward_uuid, AccountHolder.account_holder_uuid)
    ).all()

    return (
        ActivityType.get_reward_status_activity_data(
            retailer_slug=retailer_slug,
            from_campaign_slug=from_campaign_slug,
            to_campaign_slug=to_campaign_slug,
            account_holder_uuid=ah_uuid,
            activity_datetime=to_campaign_start_date,
            pending_reward_uuid=pr_uuid,
        )
        for pr_uuid, ah_uuid in updated_rewards
    )


def generate_payloads_for_delete_account_holder_activity(
    account_holders: list[AccountHolder],
    sso_username: str,
) -> Generator[dict, None, None]:  # pragma: no cover
    return (
        ActivityType.get_account_holder_deleted_activity_data(
            activity_datetime=datetime.now(tz=timezone.utc),
            account_holder_uuid=account_holder.account_holder_uuid,
            retailer_name=account_holder.retailerconfig.name,
            retailer_status=account_holder.retailerconfig.status,
            retailer_slug=account_holder.retailerconfig.slug,
            sso_username=sso_username,
        )
        for account_holder in account_holders
    )
