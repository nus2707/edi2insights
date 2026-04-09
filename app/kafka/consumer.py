# app/kafka/consumer.py
import json
from confluent_kafka import Consumer, KafkaError
from app.config import settings
from app.transformers.to_csv import write_csv
from app.cloud.s3_uploader import upload_to_s3

def run_consumer():
    consumer = Consumer({
        "bootstrap.servers": settings.kafka_bootstrap_servers,
        "group.id": settings.kafka_group_id,
        "auto.offset.reset": "earliest",
        "enable.auto.commit": False,   # manual commit for safety
    })
    consumer.subscribe([
        settings.kafka_topic_claims,
        settings.kafka_topic_eligibility,
    ])

    print("Consumer started — listening for EDI events...")

    try:
        while True:
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() != KafkaError._PARTITION_EOF:
                    print(f"Consumer error: {msg.error()}")
                continue

            payload = json.loads(msg.value().decode("utf-8"))
            topic   = msg.topic()

            # Route by topic → transform → upload
            if topic == settings.kafka_topic_claims:
                csv_path = write_csv(payload, doc_type="claims")
                upload_to_s3(csv_path, s3_key=f"claims/{payload['claim_id']}.csv")

            consumer.commit(msg)   # only commit after success
    finally:
        consumer.close()