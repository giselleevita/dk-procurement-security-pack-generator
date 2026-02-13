from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "dev"
    app_base_url: str = "http://localhost:8000"
    web_base_url: str = "http://localhost:5173"
    allowed_origins: str = ""
    allowed_hosts: str = ""

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


def parse_allowed_origins(settings: Settings) -> list[str]:
    if settings.allowed_origins.strip():
        return [o.strip() for o in settings.allowed_origins.split(",") if o.strip()]
    # Default to common local dev origins.
    return list({settings.web_base_url, "http://localhost:5173", "http://127.0.0.1:5173"})


def parse_allowed_hosts(settings: Settings) -> list[str]:
    if settings.allowed_hosts.strip():
        return [h.strip() for h in settings.allowed_hosts.split(",") if h.strip()]
    # Default for local dev + tests.
    return ["localhost", "127.0.0.1", "testserver"]
