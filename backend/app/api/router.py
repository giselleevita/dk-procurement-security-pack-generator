from fastapi import APIRouter

from app.api.routes.auth import router as auth_router
from app.api.routes.connections import router as connections_router
from app.api.routes.controls import router as controls_router
from app.api.routes.collect import router as collect_router
from app.api.routes.export import router as export_router
from app.api.routes.health import router as health_router
from app.api.routes.me import router as me_router
from app.api.routes.oauth import router as oauth_router
from app.api.routes.wipe import router as wipe_router

router = APIRouter()

router.include_router(health_router)
router.include_router(auth_router)
router.include_router(me_router)
router.include_router(oauth_router)
router.include_router(connections_router)
router.include_router(collect_router)
router.include_router(controls_router)
router.include_router(export_router)
router.include_router(wipe_router)
