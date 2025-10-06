from pydantic_settings import BaseSettings
from enum import Enum


class LogoStorageType(Enum):
    FILESYSTEM = "filesystem"
    S3 = "s3"


class Settings(BaseSettings):
    database_url: str
    JWT_SECRET: str
    LOGO_STORAGE_PATH: str = "media/logos"
    LOGO_STORAGE_TYPE: LogoStorageType = LogoStorageType.FILESYSTEM

    class Config:
        env_file = ".env"


settings = Settings()
