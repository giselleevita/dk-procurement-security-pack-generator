from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "dev"  # dev|demo|production
    runtime_sku: str = "demo"  # demo|production
    app_base_url: str = "http://localhost:8000"
    web_base_url: str = "http://localhost:5173"
    exports_dir: str = "exports"
    allowed_origins: str = ""
    allowed_hosts: str = ""
    support_sla_name: str = "best_effort"
    support_sla_response_hours: int = 48
    evidence_age_alert_days: int = 30

    cookie_secure: bool = False
    rate_limit_max_requests: int = 120
    rate_limit_window_seconds: int = 60

    # Production mode: enforced when app_env == "production".
    # In production mode startup will reject demo/placeholder Fernet keys.
    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    @property
    def is_demo_sku(self) -> bool:
        return self.runtime_sku.lower() == "demo"

    database_url: str
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_timeout_sec: int = 30
    db_pool_recycle_sec: int = 1800
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
        origins = [o.strip() for o in settings.allowed_origins.split(",") if o.strip()]
        if any(o == "*" for o in origins):
            # Cookie-auth + credentials means wildcard origins are unsafe/misleading.
            raise ValueError("ALLOWED_ORIGINS must not include '*' when using credentialed cookies")
        return origins
    # Default to common local dev origins.
    return list({settings.web_base_url, "http://localhost:5173", "http://127.0.0.1:5173"})


def parse_allowed_hosts(settings: Settings) -> list[str]:
    if settings.allowed_hosts.strip():
        return [h.strip() for h in settings.allowed_hosts.split(",") if h.strip()]
    # Default for local dev + tests.
    return ["localhost", "127.0.0.1", "testserver"]
