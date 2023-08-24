import json
import argparse
from cosmos_message_lib import (
    get_connection_and_exchange,
    verify_payload_and_send_activity,
)
from sqlalchemy.pool import NullPool
from datetime import datetime, timezone
from os import getenv
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, select, MetaData, Table

# Parse script args
parser = argparse.ArgumentParser(description="Process cleaned tx data")
parser.add_argument("-f", "--filename", help="Name of the file to process")
parser.add_argument("-d", "--dryrun", action="store_true", help="Dry run script")
args = parser.parse_args()
# Define the input file path
input_file_path = args.filename
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
##############################################
# RABBIT CONFIG
RABBITMQ_DSN = getenv("RABBITMQ_DSN", "amqp://guest:guest@localhost:5672//")
MESSAGE_EXCHANGE_NAME: str = "hubble-activities"
TX_IMPORT_ROUTING_KEY: str = "activity.vela.tx.import"
TX_HISTORY_ROUTING_KEY: str = "activity.vela.tx.processed"
##############################################

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

# RabbitMQ connection
connection, exchange = get_connection_and_exchange(
    rabbitmq_dsn=RABBITMQ_DSN,
    message_exchange_name=MESSAGE_EXCHANGE_NAME,
)

# Table bindings
metadata = MetaData()
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


def sync_send_activity(payload: dict, *, routing_key: str) -> None:
    verify_payload_and_send_activity(connection, exchange, payload, routing_key)


# Read the JSON file and load data into memory
with open(input_file_path, "r") as json_file:
    data = json.load(json_file)

tx_history_event_count = 0
tx_import_event_count = 0

tx_ids = set()

for event in data:
    transaction_id = event["activity_identifier"]
    # Check polaris and hubble to make sure transaction_id doesn't exist
    with HubbleSyncSessionMaker() as hubble_db_session, PolarisSyncSessionMaker() as polaris_db_session:
        # Query polaris table
        polaris_result = polaris_db_session.execute(
            select(AccountHolderTransactionHistory.c.id).where(
                AccountHolderTransactionHistory.c.transaction_id == transaction_id
            )
        ).one_or_none()

        # Query hubble table
        hubble_result = (
            hubble_db_session.execute(select(Activity.c.id).where(Activity.c.activity_identifier == transaction_id))
            .scalars()
            .all()
        )

    if not polaris_result and not hubble_result:
        tx_ids.add(transaction_id)

        match event["type"]:
            case "TX_IMPORT":
                tx_import_event_count += 1
                routing_key = TX_IMPORT_ROUTING_KEY
            case "TX_HISTORY":
                tx_history_event_count += 1
                routing_key = TX_HISTORY_ROUTING_KEY
            case _:
                raise ValueError("Cannot send for this type")

        # Formatting
        event["datetime"] = datetime.strptime(event["datetime"], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
        event["underlying_datetime"] = datetime.strptime(event["underlying_datetime"], "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc
        )

        if not dry_run:
            sync_send_activity(event, routing_key=routing_key)
        else:
            print(f"Will enqueue event with transaction_id: {transaction_id}")

if not dry_run:
    print(f"tx_ids for events queued: {list(tx_ids)}")
    print(f"No. of TX_IMPORT events queued: {tx_import_event_count}")
    print(f"No. of TX_HISTORY events queued: {tx_history_event_count}")
else:
    print(f"tx_ids for events to be queued: {list(tx_ids)}")
    print(f"No. of TX_IMPORT events to be queued: {tx_import_event_count}")
    print(f"No. of TX_HISTORY events to be queued: {tx_history_event_count}")
