from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    api_key: str = "test-key-123"

    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_group_id: str = "edi2insights-consumers"
    kafka_topic_claims: str = "edi-837p-claims"
    kafka_topic_eligibility: str = "edi-270-eligibility"

    duckdb_path: str = "data/edi2insights.duckdb"

    model_config = {"env_file": ".env"}


settings = Settings()
