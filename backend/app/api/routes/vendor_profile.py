from __future__ import annotations

from datetime import datetime

from email_validator import EmailNotValidError
from email_validator import validate_email as _validate_email
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, get_auth_ctx, require_csrf
from app.db.session import get_db
from app.repos.vendor_profile import get_vendor_profile, upsert_vendor_profile

router = APIRouter(tags=["vendor-profile"])


class VendorProfileResponse(BaseModel):
    company_name: str
    cvr_number: str
    address: str
    contact_name: str
    contact_email: str
    contact_phone: str
    security_officer_name: str
    security_officer_title: str
    pack_scope: str
    pack_recipient: str
    pack_validity_months: int
    updated_at: datetime | None = None


class VendorProfileUpdate(BaseModel):
    company_name: str = Field(default="", max_length=255)
    cvr_number: str = Field(default="", max_length=8, pattern=r"^\d{0,8}$")
    address: str = Field(default="", max_length=500)
    contact_name: str = Field(default="", max_length=255)
    # Allow empty string or a valid e-mail address.
    contact_email: str = Field(default="", max_length=320)
    # International phone numbers: digits, spaces, +, -, (, ), .
    contact_phone: str = Field(default="", max_length=50, pattern=r"^[\+\d\s\-\(\)\.]{0,50}$")
    security_officer_name: str = Field(default="", max_length=255)
    security_officer_title: str = Field(default="", max_length=255)
    pack_scope: str = Field(default="", max_length=1000)
    pack_recipient: str = Field(default="", max_length=500)
    pack_validity_months: int = Field(default=6, ge=1, le=60)

    @field_validator("contact_email")
    @classmethod
    def validate_contact_email(cls, v: str) -> str:
        """Accept empty string (field not filled) or a syntactically valid e-mail."""
        if not v:
            return v
        try:
            info = _validate_email(v, check_deliverability=False)
            return info.normalized
        except EmailNotValidError as exc:
            raise ValueError(str(exc)) from exc


def _to_response(vp) -> VendorProfileResponse:
    return VendorProfileResponse(
        company_name=vp.company_name,
        cvr_number=vp.cvr_number,
        address=vp.address,
        contact_name=vp.contact_name,
        contact_email=vp.contact_email,
        contact_phone=vp.contact_phone,
        security_officer_name=vp.security_officer_name,
        security_officer_title=vp.security_officer_title,
        pack_scope=vp.pack_scope,
        pack_recipient=vp.pack_recipient,
        pack_validity_months=vp.pack_validity_months,
        updated_at=vp.updated_at,
    )


@router.get("/vendor-profile", response_model=VendorProfileResponse)
def get_profile(
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_ctx),
) -> VendorProfileResponse:
    vp = get_vendor_profile(db, user_id=auth.user.id)
    if vp is None:
        return VendorProfileResponse(
            company_name="",
            cvr_number="",
            address="",
            contact_name="",
            contact_email="",
            contact_phone="",
            security_officer_name="",
            security_officer_title="",
            pack_scope="",
            pack_recipient="",
            pack_validity_months=6,
        )
    return _to_response(vp)


@router.put("/vendor-profile", response_model=VendorProfileResponse)
def update_profile(
    body: VendorProfileUpdate,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_ctx),
    _: None = Depends(require_csrf),
) -> VendorProfileResponse:
    vp = upsert_vendor_profile(db, user_id=auth.user.id, data=body.model_dump())
    return _to_response(vp)
