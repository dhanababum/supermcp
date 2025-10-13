from pydantic_settings import BaseSettings


class SqlDbConfig(BaseSettings):
    API_URL: str = "http://localhost:9000"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
