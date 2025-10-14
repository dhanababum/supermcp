from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    app_base_url: str = "http://localhost:9000"
    app_web_url: str = "http://localhost:3000"
    connector_secret: str
    connector_id: str
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False, extra="forbid"
    )


settings = Settings()
