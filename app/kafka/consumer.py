import json
import logging
from confluent_kafka import Consumer, KafkaException, KafkaError
from app.config import settings
from app.transformers.claims_transformer import store_claim
from app.transformers.eligibility_transformer import store_inquiry

logger = logging.getLogger(__name__)


def run_consumer():
    consumer = Consumer({
        "bootstrap.servers": settings.kafka_bootstrap_servers,
        "group.id":          settings.kafka_group_id,
        "auto.offset.reset": "earliest",
        "enable.auto.commit": False,
    })
    consumer.subscribe([settings.kafka_topic_claims, settings.kafka_topic_eligibility])
    logger.info("Consumer started — subscribed to %s and %s",
                settings.kafka_topic_claims, settings.kafka_topic_eligibility)

    try:
        while True:
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                raise KafkaException(msg.error())

            try:
                payload = json.loads(msg.value().decode("utf-8"))
            except Exception:
                logger.warning("Could not decode message on %s", msg.topic())
                consumer.commit(msg)
                continue

            topic = msg.topic()
            try:
                if topic == settings.kafka_topic_claims:
                    store_claim(payload)
                    logger.info("Stored claim %s from Kafka", payload.get("claim_id"))
                elif topic == settings.kafka_topic_eligibility:
                    store_inquiry(payload)
                    logger.info("Stored inquiry %s from Kafka", payload.get("inquiry_id"))
            except Exception as exc:
                logger.error("Failed to store message from %s: %s", topic, exc)

            consumer.commit(msg)

    except KeyboardInterrupt:
        logger.info("Consumer stopped.")
    finally:
        consumer.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
    run_consumer()
