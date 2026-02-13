from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr

from app.api.deps import AuthContext, get_auth_ctx

router = APIRouter(tags=["auth"])


class MeResponse(BaseModel):
    id: str
    email: EmailStr
    created_at: datetime


@router.get("/me", response_model=MeResponse)
def me(auth: AuthContext = Depends(get_auth_ctx)) -> MeResponse:
    u = auth.user
    return MeResponse(id=str(u.id), email=u.email, created_at=u.created_at)

