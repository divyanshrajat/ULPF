from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "ULPF MVP"
    API_V1_STR: str = "/api/v1"

    # Runtime mode: internet | airgap
    ULPF_MODE: str = "internet"

    DATABASE_URL: str | None = None

    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "ulpf"
    POSTGRES_PASSWORD: str = "ulpf"
    POSTGRES_DB: str = "ulpf"
    POSTGRES_PORT: str = "5432"

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    REDIS_URI: str = "redis://localhost:6379/0"

    # Vault & storage (supports local fallback on Windows)
    VAULT_DIR: str = os.getenv("VAULT_DIR", os.path.abspath("./data/vault"))

    # OpenSearch
    OPENSEARCH_URI: str = "http://localhost:9200"
    OPENSEARCH_INDEX: str = "ulpf-events"

    # Local AI model (air-gap safe)
    # Must point to a locally pre-downloaded SentenceTransformer model directory.
    # Never falls back to a remote download at runtime.
    ULPF_MODEL_PATH: str = "all-MiniLM-L6-v2"

    # Processing thresholds (from TRD)
    MAPPING_REVIEW_FLOOR: float = 0.65
    MAPPING_AUTO_ACCEPT: float = 0.90

    # Drain3 configuration (from TRD)
    DRAIN3_SIM_TH: float = 0.4
    DRAIN3_DEPTH: int = 4
    DRAIN3_MAX_CHILDREN: int = 100
    DRAIN3_MAX_TEMPLATES: int = 500

    # Auth
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "ulpf-admin"
    SECRET_KEY: str = "changeme-in-production-minimum-32-characters"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

settings = Settings()
