from fastapi import APIRouter

from app.core.settings import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    settings = get_settings()
    is_demo = settings.app_env == "demo"
    return {
        "status": "ok",
        "demo_mode": is_demo,
        "demo_email": settings.demo_email if is_demo else None,
    }

