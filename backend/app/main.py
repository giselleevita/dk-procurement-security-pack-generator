from __future__ import annotations

import logging
import time
import uuid as _uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.router import router as api_router
from app.core.limiter import limiter
from app.core.settings import get_settings, parse_allowed_hosts, parse_allowed_origins

logger = logging.getLogger("dkpack")

# Explicit header allowlist — avoids the credential-leak risk of allow_headers=["*"].
_CORS_ALLOW_HEADERS = [
    "content-type",
    "x-csrf-token",
    "accept",
    "accept-language",
    "cache-control",
    "pragma",
]

# Content-Security-Policy that restricts sources to same-origin.
# Allows inline styles because Vite injects them in dev mode; tighten for prod.
_CSP = (
    "default-src 'self'; "
    "script-src 'self'; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data:; "
    "font-src 'self'; "
    "connect-src 'self'; "
    "frame-ancestors 'none'; "
    "base-uri 'self'; "
    "form-action 'self';"
)


def create_app() -> FastAPI:
    settings = get_settings()

    # ── Logging ─────────────────────────────────────────────────────────────
    logging.basicConfig(
        level=logging.INFO,
        format='{"ts":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","msg":"%(message)s"}',
        datefmt="%Y-%m-%dT%H:%M:%SZ",
    )

    # ── Lifespan (startup tasks) ─────────────────────────────────────────────
    @asynccontextmanager
    async def _lifespan(_app: FastAPI):
        from app.services.pack_signing import ensure_signing_material

        ensure_signing_material()

        if settings.app_env == "demo":
            from app.db.session import _sessionmaker
            from app.services.demo_seed import seed_demo_data

            db = _sessionmaker()()
            try:
                seed_demo_data(
                    db,
                    demo_email=settings.demo_email,
                    demo_password=settings.demo_password,
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning("Demo seed failed (non-fatal): %s", exc)
            finally:
                db.close()

        yield  # application runs

    # ── FastAPI app ──────────────────────────────────────────────────────────
    app = FastAPI(
        title="DK Procurement Security Pack Generator",
        version="0.2.0",
        lifespan=_lifespan,
        docs_url="/api/docs" if settings.app_env == "dev" else None,
        redoc_url="/api/redoc" if settings.app_env == "dev" else None,
        openapi_url="/api/openapi.json" if settings.app_env == "dev" else None,
    )

    # ── Rate limiting ────────────────────────────────────────────────────────
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    # ── Host + CORS ──────────────────────────────────────────────────────────
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=parse_allowed_hosts(settings))
    app.add_middleware(
        CORSMiddleware,
        allow_origins=parse_allowed_origins(settings),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=_CORS_ALLOW_HEADERS,
    )

    # ── Request-ID + structured access log ──────────────────────────────────
    @app.middleware("http")
    async def request_context_middleware(request: Request, call_next) -> Response:
        request_id = str(_uuid.uuid4())
        request.state.request_id = request_id
        t0 = time.perf_counter()

        response: Response = await call_next(request)

        latency_ms = round((time.perf_counter() - t0) * 1000, 1)
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "method=%s path=%s status=%s latency_ms=%.1f rid=%s",
            request.method,
            request.url.path,
            response.status_code,
            latency_ms,
            request_id,
        )
        return response

    # ── Security response headers ────────────────────────────────────────────
    @app.middleware("http")
    async def security_headers(request: Request, call_next) -> Response:
        resp: Response = await call_next(request)
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("Referrer-Policy", "no-referrer")
        resp.headers.setdefault("X-Frame-Options", "DENY")
        resp.headers.setdefault("X-XSS-Protection", "0")  # CSP is the modern standard
        resp.headers.setdefault("Permissions-Policy", "geolocation=(), camera=(), microphone=()")
        resp.headers.setdefault("Content-Security-Policy", _CSP)
        if settings.app_env == "prod":
            # Only set HSTS when actually serving over HTTPS.
            resp.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=31536000; includeSubDomains; preload",
            )
        return resp

    app.include_router(api_router, prefix="/api")
    return app


app = create_app()
