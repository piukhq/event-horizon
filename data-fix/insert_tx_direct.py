import argparse

from os import getenv

from cosmos_message_lib.schemas import ActivitySchema, utc_datetime
from pydantic import BaseModel, Field
from sqlalchemy import MetaData, Table, create_engine, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

# Parse script args
parser = argparse.ArgumentParser(description="Process cleaned tx data")
parser.add_argument("-d", "--dryrun", action="store_true", help="Dry run script")
args = parser.parse_args()
# Check dryrun mode
dry_run = args.dryrun if args.dryrun is not None else False

#####################################
# DB Config
USE_NULL_POOL: bool = False
TESTING: bool = False

null_pool = {"poolclass": NullPool} if USE_NULL_POOL or TESTING else {}

# application_name
POLARIS_CONNECT_ARGS = {"application_name": "polaris"}
HUBBLE_CONNECT_ARGS = {"application_name": "hubble"}
SQL_DEBUG: bool = False

# Polaris DB
POLARIS_DATABASE_URI = getenv("POLARIS_DATABASE_URI", "postgresql://postgres:pass@localhost:5552/polaris")

DATABASE_URI = getenv("DATABASE_URI", "postgresql://postgres:pass@localhost:5552/{}")
HUBBLE_DATABASE_URI = DATABASE_URI.format("hubble")
#####################################

polaris_sync_engine = create_engine(
    POLARIS_DATABASE_URI,
    connect_args=POLARIS_CONNECT_ARGS,
    pool_pre_ping=True,
    echo=SQL_DEBUG,
    future=True,
    **null_pool,
)
PolarisSyncSessionMaker = sessionmaker(bind=polaris_sync_engine, future=True, expire_on_commit=False)

# Hubble DB
hubble_sync_engine = create_engine(
    HUBBLE_DATABASE_URI,
    connect_args=HUBBLE_CONNECT_ARGS,
    pool_pre_ping=True,
    echo=SQL_DEBUG,
    future=True,
    **null_pool,
)
HubbleSyncSessionMaker = sessionmaker(bind=hubble_sync_engine, future=True, expire_on_commit=False)

# Table bindings
metadata = MetaData()
AccountHolder = Table(
    "account_holder",
    metadata,
    autoload_with=polaris_sync_engine,
)
AccountHolderTransactionHistory = Table(
    "account_holder_transaction_history",
    metadata,
    autoload_with=polaris_sync_engine,
)
Activity = Table(
    "activity",
    metadata,
    autoload_with=hubble_sync_engine,
)

# Staging for testing
TX_IDS_TO_FETCH = (
    "202307311322",
    "202307311351",
    "202307311326",
    "202307311323",
    "202307311358",
    "202307311360",
    "202307311352",
    "202307311361",
    "202307311356",
    "202307311349",
    "202307311321",
    "202307311325",
    "202307311324",
    "202307311350",
    "202307311355",
    "202307311359",
    "202307311357",
)

# PROD
# TX_IDS_TO_FETCH = [
#     "bpl-viator-c4a13f2f52ee0078198ccafa57119ba28b989a70",
#     "bpl-viator-44e7cc414e85357e15485fc96ec730938b20ea0e",
#     "bpl-viator-7bb7f3bfe22515f73daff27276812e4b0cb3cc90",
#     "bpl-viator-620fa02496eb299212b7e82b385ce8070a84b3fd",
#     "bpl-viator-b19c4e0aecc80fb3306adaed67498813353bc0cb",
#     "bpl-viator-838a8c69ab2203eefd2c64ac5633ef19a9cef7f1",
#     "bpl-viator-1361fb5fe825db28debbb66946ee1c3483e6d92b",
#     "bpl-viator-cc49c77366ad1ed45c53e52735f6268c2bd47d67",
#     "bpl-viator-b2b1be66e5a0240f25d9e1e5d1ca846ff2bb53cf",
#     "bpl-viator-16f3c6ea65d0c45b4fa023277e533ebd544414d9",
#     "bpl-viator-801c87255f4b08e08effbe91ba78287b544bb898",
#     "bpl-viator-991ff572b1f6aecd66f5c5c6bef8cc359dd849aa",
# ]


class EarnedSchema(BaseModel):
    value: str
    type: str  # noqa: A003


class TransactionHistorySchema(BaseModel):
    transaction_id: str
    datetime: utc_datetime
    amount: str
    amount_currency: str
    location_name: str = Field(..., alias="store_name")
    earned: list[EarnedSchema]


def fetch_activities_for_ids() -> list:
    with HubbleSyncSessionMaker() as hubble_db_session:
        stmt = select(Activity).where(Activity.c.activity_identifier.in_(TX_IDS_TO_FETCH))
        result = hubble_db_session.execute(stmt).fetchall()
        return result


def insert_tx_history_polairs(payload: TransactionHistorySchema, account_holder_uuid: str) -> bool:
    with PolarisSyncSessionMaker() as polaris_db_session:
        result = polaris_db_session.execute(
            select(AccountHolderTransactionHistory.c.id).where(
                AccountHolderTransactionHistory.c.transaction_id == payload.transaction_id
            )
        ).one_or_none()

    if not result:
        if dry_run:
            print(f"Will insert missing tx history with transaction_id: {payload.transaction_id}")
            return False
        else:
            values_to_insert = payload.dict()
            result = polaris_db_session.execute(
                insert(AccountHolderTransactionHistory)
                .on_conflict_do_nothing()
                .values(
                    account_holder_id=select(AccountHolder.c.id)
                    .where(AccountHolder.c.account_holder_uuid == account_holder_uuid)
                    .scalar_subquery(),
                    **values_to_insert,
                )
                .returning(AccountHolderTransactionHistory.c.id)
            )
            try:
                polaris_db_session.commit()
                return bool(result.all())
            except Exception as ex:
                print(f"Failed to insert tx history with id: {payload.transaction_id}")
                return False
    else:
        print(f"Found matching record in Transaction history table with transaction_id: {payload.transaction_id}")
        return False


def main() -> None:
    activities = fetch_activities_for_ids()

    inserted_count = 0
    for activity in activities:
        validated = ActivitySchema(**activity)
        if validated.type == "TX_IMPORT":
            continue

        account_holder_uuid = validated.user_id
        payload = TransactionHistorySchema(**validated.data)

        inserted = insert_tx_history_polairs(payload, account_holder_uuid)
        if inserted:
            inserted_count += 1

    print(f"Total tx history inserted to polaris: {inserted_count}")


main()
