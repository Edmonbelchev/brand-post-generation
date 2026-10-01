from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    brand_voice_threshold: int = 80
    llm_timeout_seconds: float = 30.0
    llm_max_tokens_generate: int = 1200
    generation_min_words: int = 180
    generation_max_words: int = 320
    audit_db_path: str = "./data/audit.db"


settings = Settings()
