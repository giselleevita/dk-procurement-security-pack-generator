from fastapi import APIRouter

from app.services.pack_signing import signing_readiness

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "signing": signing_readiness()}
