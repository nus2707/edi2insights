# app/kafka/consumer.py
import json
from confluent_kafka import Consumer, KafkaException, KafkaError
from app.config import settings


def run_consumer():
    consumer_conf = {
        "bootstrap.servers": settings.kafka_bootstrap_servers,
        "group.id": settings.kafka_group_id,
        "auto.offset.reset": "earliest",
        "enable.auto.commit": False
    }

    consumer = Consumer(consumer_conf)

    # Subscribe to your actual topics
    consumer.subscribe(["edi-837p-claims", "edi-270-eligibility"])

    print("Consumer started — waiting for EDI messages...\n")

    try:
        while True:
            msg = consumer.poll(timeout=1.0)

            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    raise KafkaException(msg.error())

            key = msg.key().decode("utf-8") if msg.key() else None
            try:
                value = json.loads(msg.value().decode("utf-8"))
            except Exception:
                value = msg.value().decode("utf-8")

            print("=" * 60)
            print(f"Topic     : {msg.topic()}")
            print(f"Partition : {msg.partition()}")
            print(f"Offset    : {msg.offset()}")
            print(f"Key       : {key}")
            print("Payload   :")
            print(json.dumps(value, indent=2))
            print("=" * 60 + "\n")

            consumer.commit(msg)

    except KeyboardInterrupt:
        print("Consumer stopped.")
    finally:
        consumer.close()


if __name__ == "__main__":
    run_consumer()