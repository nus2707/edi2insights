# app/kafka/producer.py
import json
from confluent_kafka import Producer
from app.config import settings

_producer: Producer | None = None

def get_producer() -> Producer:
    global _producer
    if _producer is None:
        _producer = Producer({
            "bootstrap.servers": settings.kafka_bootstrap_servers,
            "acks": "all",            # wait for all replicas
            "retries": 3,
            "compression.type": "gzip",
        })
    return _producer

async def publish_event(topic: str, key: str, value: dict) -> None:
    producer = get_producer()

    def delivery_report(err, msg):
        if err:
            print(f"Delivery failed: {err}")
        else:
            print(f"Delivered to {msg.topic()} [{msg.partition()}]")

    producer.produce(
        topic=topic,
        key=key.encode("utf-8"),
        value=json.dumps(value).encode("utf-8"),
        on_delivery=delivery_report,
    )
    producer.poll(0)   # trigger delivery callbacks
    producer.flush()   # wait until message is sent