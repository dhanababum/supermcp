from pydantic_settings import BaseSettings
from typing import Optional


class Config(BaseSettings):
    app_base_url: str = "http://localhost:9000"
    app_web_url: str = "http://localhost:3000"

    class Config:
        env_file = ".env"
        extra = "allow"
        case_sensitive = False


settings = Config()
