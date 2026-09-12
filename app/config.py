"""Configuration de l'application, chargée depuis l'environnement ou un `.env`."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./esg.db"


settings = Settings()
