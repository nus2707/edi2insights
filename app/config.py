from pydantic import BaseSettings

class Settings(BaseSettings):
    kafka_bootstrap_servers: str
    kafka_topic_claims: str
    kafka_topic_eligibility: str

    class Config:
        env_file = ".env"   # tells Pydantic to load from your .env file

settings = Settings()