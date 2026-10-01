import os

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _running_on_vercel() -> bool:
    return os.environ.get("VERCEL", "").lower() in ("1", "true", "yes")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    brand_voice_threshold: int = 80
    llm_timeout_seconds: float = 30.0
    llm_max_tokens_generate: int = 1200
    generation_min_words: int = 180
    generation_max_words: int = 320
    audit_db_path: str = "/tmp/audit.db" if _running_on_vercel() else "./data/audit.db"

    @field_validator("audit_db_path")
    @classmethod
    def vercel_writable_audit_path(cls, value: str) -> str:
        """Vercel serverless FS is read-only except /tmp."""
        if not _running_on_vercel():
            return value
        if value.startswith("/tmp"):
            return value
        return "/tmp/audit.db"


settings = Settings()
