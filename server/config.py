import os
from typing import List, Union
from pydantic import AnyHttpUrl, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

class Settings(BaseSettings):
    """
    應用程式設定類別，使用 Pydantic BaseSettings 進行管理。
    """
    # Environment Setting
    APP_ENV: str = "production"

    # API Setting
    PROJECT_NAME: str = "QoLScope API"
    API_VERSION: str = "0.0.1"

    # CORS Setting
    CORS_ORIGINS: Union[List[AnyHttpUrl], str] = ["https://qolscope.onrender.com"]

    # Cache Setting
    CACHE_PREFIX: str = "rental-cache"

    # Google API Key
    MAPS_API_KEY: str

    # Database Setting
    DB_HOST: str
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    DB_PORT: int

    @property
    def database_url(self) -> PostgresDsn:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(__file__), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()