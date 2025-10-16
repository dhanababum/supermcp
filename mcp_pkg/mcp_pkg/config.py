from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_base_url: str
    app_web_url: str
    connector_secret: str
    connector_id: str
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="forbid"
    )


settings = Settings()
