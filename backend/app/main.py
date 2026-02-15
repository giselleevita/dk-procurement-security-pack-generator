from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.api.router import router as api_router
from app.services.pack_signing import ensure_signing_material
from app.core.settings import get_settings, parse_allowed_hosts, parse_allowed_origins


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="DK Procurement Security Pack Generator",
        version="0.1.0",
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

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        resp: Response = await call_next(request)
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("Referrer-Policy", "no-referrer")
        resp.headers.setdefault("X-Frame-Options", "DENY")
        return resp

    @app.on_event("startup")
    async def _ensure_pack_signing_key() -> None:
        # Creates signing material on disk if missing (no external calls).
        ensure_signing_material()

    app.include_router(api_router, prefix="/api")
    return app


app = create_app()
