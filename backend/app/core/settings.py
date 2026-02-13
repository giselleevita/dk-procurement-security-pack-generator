from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "dev"
    app_base_url: str = "http://localhost:8000"
    web_base_url: str = "http://localhost:5173"

    cookie_secure: bool = False

    database_url: str
    fernet_key: str

    github_client_id: str = ""
    github_client_secret: str = ""
    github_oauth_redirect_uri: str = ""

    ms_client_id: str = ""
    ms_client_secret: str = ""
    ms_tenant: str = "organizations"
    ms_oauth_redirect_uri: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]

