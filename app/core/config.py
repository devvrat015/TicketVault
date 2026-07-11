from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str
    DEBUG: bool
    DATABASE_URL: str

    model_config = SettingsConfigDict(
        env_file=".env"
    )

settings = Settings()