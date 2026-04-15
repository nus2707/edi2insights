# app/config.py
from pydantic import BaseSettings

class Settings(BaseSettings):
    # Kafka connection
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_group_id: str = "edi2insights-consumers"

    # Kafka topics
    kafka_topic_claims: str = "edi-837p-claims"
    kafka_topic_eligibility: str = "edi-270-eligibility"

    class Config:
        env_file = ".env"   # optional, loads values from a .env file


settings = Settings()