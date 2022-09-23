from cosmos_message_lib import get_connection_and_exchange, verify_payload_and_send_activity

from app.settings import MESSAGE_EXCHANGE_NAME, RABBITMQ_DSN

connection, exchange = get_connection_and_exchange(
    rabbitmq_dsn=RABBITMQ_DSN,
    message_exchange_name=MESSAGE_EXCHANGE_NAME,
)


def sync_send_activity(payload: dict, *, routing_key: str) -> None:
    verify_payload_and_send_activity(connection, exchange, payload, routing_key)
