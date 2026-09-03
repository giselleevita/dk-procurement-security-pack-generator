from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.requests import Request
from starlette.responses import Response
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.api.router import router as api_router
from app.api.middleware.security import SecurityMiddleware
from app.services.pack_signing import ensure_signing_material
from app.core.settings import get_settings, parse_allowed_hosts, parse_allowed_origins


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="DK Procurement Security Pack Generator",
        version="1.1.1",
        docs_url="/api/docs" if settings.app_env == "dev" else None,
        redoc_url="/api/redoc" if settings.app_env == "dev" else None,
        openapi_url="/api/openapi.json" if settings.app_env == "dev" else None,
    )

    app.add_middleware(TrustedHostMiddleware, allowed_hosts=parse_allowed_hosts(settings))

    app.add_middleware(
        CORSMiddleware,
        allow_origins=parse_allowed_origins(settings),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    app.add_middleware(GZipMiddleware, minimum_size=1024)
    app.add_middleware(
        SecurityMiddleware,
        max_requests=settings.rate_limit_max_requests,
        window_seconds=settings.rate_limit_window_seconds,
    )

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        resp: Response = await call_next(request)
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("Referrer-Policy", "no-referrer")
        resp.headers.setdefault("X-Frame-Options", "DENY")
        resp.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        resp.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; connect-src 'self'; img-src 'self' data:; "
            "style-src 'self' 'unsafe-inline'; object-src 'none'; frame-ancestors 'none'",
        )
        return resp

    @app.on_event("startup")
    async def _ensure_pack_signing_key() -> None:
        # Creates signing material on disk if missing (no external calls).
        ensure_signing_material()

    @app.on_event("startup")
    async def _validate_production_mode() -> None:
        """DK-1-2: Reject demo/placeholder Fernet keys in production mode."""
        if not settings.is_production:
            return
        if settings.is_demo_sku:
            raise RuntimeError(
                "Production mode (APP_ENV=production) requires RUNTIME_SKU=production. "
                "Refusing to start with the demo SKU enabled."
            )
        _DEMO_KEY_MARKERS = ("demo", "test", "example", "placeholder", "changeme", "secret")
        key_lower = settings.fernet_key.lower()
        if any(marker in key_lower for marker in _DEMO_KEY_MARKERS):
            raise RuntimeError(
                "Production mode (APP_ENV=production) requires a real Fernet key. "
                "The configured FERNET_KEY contains a demo/placeholder value. "
                "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
            )
        # Minimum key length check (Fernet keys are 44 base64-char URL-safe strings).
        if len(settings.fernet_key.strip()) < 44:
            raise RuntimeError(
                "Production mode (APP_ENV=production) requires a valid 44-character base64 Fernet key."
            )

    app.include_router(api_router, prefix="/api")
    static_dir = Path(__file__).resolve().parent / "static"
    if static_dir.exists():
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="demo-ui")
    return app


app = create_app()
