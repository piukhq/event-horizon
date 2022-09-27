from sqlalchemy import func, literal
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.future import select

from event_horizon.polaris.db import AccountHolderCampaignBalance, db_session


def balance_transfer(
    *, from_campaign_slug: str, to_campaign_slug: str, min_balance: int, rate_percent: int, loyalty_type: str
) -> None:  # pragma: no cover
    rate_multiplier = rate_percent / 100

    match loyalty_type:
        case "ACCUMULATOR":
            computed_balance = func.ceil(AccountHolderCampaignBalance.balance * rate_multiplier)
        case "STAMPS":
            computed_balance = func.ceil((AccountHolderCampaignBalance.balance * rate_multiplier) / 100) * 100
        case _:
            raise ValueError(f"Unexpected loyalty type '{loyalty_type}' received. Expected ACCUMULATOR or STAMPS.")

    insert_values_stmt = select(
        literal(to_campaign_slug).label("literal_slug"),
        AccountHolderCampaignBalance.account_holder_id,
        computed_balance.label("computed_balance"),
    ).where(
        AccountHolderCampaignBalance.campaign_slug == from_campaign_slug,
        AccountHolderCampaignBalance.balance >= min_balance,
        AccountHolderCampaignBalance.balance > 0,
    )
    insert_stmt = insert(AccountHolderCampaignBalance).from_select(
        ["campaign_slug", "account_holder_id", "balance"], insert_values_stmt
    )
    upsert_stmt = insert_stmt.on_conflict_do_update(
        index_elements=["account_holder_id", "campaign_slug"],
        set_={"balance": AccountHolderCampaignBalance.balance + insert_stmt.excluded.balance},
    )
    db_session.execute(upsert_stmt)
    db_session.commit()
