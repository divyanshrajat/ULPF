import os

from pydantic_settings import BaseSettings, SettingsConfigDict


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

    QUEUE_BACKEND: str = "redis"  # "redis" | "memory" (dev/test fallback)

    # ReDoS protection: hard CPU timeout for the Python re fallback (subprocess isolation)
    REGEX_TIMEOUT_SECONDS: float = 2.0
    REDIS_URI: str = "redis://localhost:6379/0"

    # Vault & storage (supports local fallback on Windows)
    VAULT_DIR: str = os.getenv("VAULT_DIR", os.path.abspath("./data/vault"))

    # OpenSearch
    OPENSEARCH_URI: str = "http://localhost:9200"
    OPENSEARCH_INDEX: str = "ulpf-events"
    OPENSEARCH_USERNAME: str | None = None
    OPENSEARCH_PASSWORD: str | None = None

    # Local AI model (air-gap safe)
    # Must point to a locally pre-downloaded GGUF model file.
    ULPF_MODEL_PATH: str = "/models/Qwen2.5-Coder-7B-Instruct-Q4_K_M.gguf"
    ULPF_MOCK_LLM: bool = False
    ULPF_SEED_DEMO_DATA: bool = False

    # Auth
    ADMIN_USERNAME: str = "admin"
    
    # Secrets - No unsafe defaults in production
    ADMIN_PASSWORD: str | None = None
    SECRET_KEY: str | None = None
    MASK_HMAC_KEY: str | None = None
    
    def validate_secrets(self):
        if self.ULPF_MODE == "dev":
            self.ADMIN_PASSWORD = self.ADMIN_PASSWORD or "ulpf-admin"
            self.SECRET_KEY = self.SECRET_KEY or "changeme-in-production-minimum-32-characters"
            self.MASK_HMAC_KEY = self.MASK_HMAC_KEY or "changeme-mask-key-minimum-32-chars"
        
        if not self.ADMIN_PASSWORD or len(self.ADMIN_PASSWORD) < 8 or self.ADMIN_PASSWORD == "ulpf-admin" and self.ULPF_MODE != "dev":
            raise ValueError("Unsafe ADMIN_PASSWORD in production")
        if not self.SECRET_KEY or len(self.SECRET_KEY) < 32 or self.SECRET_KEY == "changeme-in-production-minimum-32-characters" and self.ULPF_MODE != "dev":
            raise ValueError("Unsafe SECRET_KEY in production")
        if not self.MASK_HMAC_KEY or len(self.MASK_HMAC_KEY) < 32 or self.MASK_HMAC_KEY == "changeme-mask-key-minimum-32-chars" and self.ULPF_MODE != "dev":
            raise ValueError("Unsafe MASK_HMAC_KEY in production")

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")

settings = Settings()
settings.validate_secrets()
