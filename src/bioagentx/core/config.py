from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "BioAgentX"
    app_env: Literal["development", "test", "staging", "production"] = "development"
    log_level: str = "INFO"

    database_url: str = ""
    use_database: bool = True
    auto_create_schema: bool = True

    embedding_dimensions: int = 64
    retrieval_limit: int = 8
    rerank_limit: int = 5
    graph_depth: int = 2

    cache_ttl_seconds: int = 300
    rate_limit_per_minute: int = 120
    rate_limit_burst: int = 40
    supported_domains: list[str] = Field(default_factory=lambda: ["oncology", "genomics", "clinical_trials"])

    @field_validator("supported_domains", mode="before")
    @classmethod
    def parse_domains(cls, value: object) -> list[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        return ["oncology", "genomics", "clinical_trials"]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
