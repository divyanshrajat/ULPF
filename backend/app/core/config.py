from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    PROJECT_NAME: str = "ULPF MVP"
    API_V1_STR: str = "/api/v1"
    
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "ulpf"
    POSTGRES_PASSWORD: str = "ulpf"
    POSTGRES_DB: str = "ulpf"
    POSTGRES_PORT: str = "5432"
    
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    REDIS_URI: str = "redis://localhost:6379/0"
    
    VAULT_DIR: str = "/data/vault" # Used inside docker, local for dev
    OPENSEARCH_URI: str = "http://localhost:9200"
    
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

settings = Settings()
