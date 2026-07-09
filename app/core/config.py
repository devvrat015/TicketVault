from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str
    DEBUG: bool

    model_config = SettingsConfigDict(
        env_file=".env"
    )