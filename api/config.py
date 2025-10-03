from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    JWT_SECRET: str

    class Config:
        env_file = ".env"


settings = Settings()
