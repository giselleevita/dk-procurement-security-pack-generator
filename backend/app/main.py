from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import router as api_router
from app.core.settings import get_settings


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="DK Procurement Security Pack Generator",
        version="0.1.0",
        docs_url="/api/docs" if settings.app_env == "dev" else None,
        redoc_url="/api/redoc" if settings.app_env == "dev" else None,
        openapi_url="/api/openapi.json" if settings.app_env == "dev" else None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.web_base_url],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix="/api")
    return app


app = create_app()
