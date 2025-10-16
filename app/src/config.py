from pydantic_settings import BaseSettings
from enum import Enum


class LogoStorageType(Enum):
    FILESYSTEM = "filesystem"
    S3 = "s3"


class Settings(BaseSettings):
    CONNECTOR_SALT: str
    ASYNC_DATABASE_URL: str
    JWT_SECRET: str
    JWT_ALGO: str
    LOGO_STORAGE_PATH: str = "media/logos"
    LOGO_STORAGE_TYPE: LogoStorageType = LogoStorageType.FILESYSTEM
    SUPERUSER_EMAIL: str | None = None
    SUPERUSER_PASSWORD: str | None = None
    WEB_URL: str | None = None

    class Config:
        case_sensitive = False
        env_file = ".env"


settings = Settings()
