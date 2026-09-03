from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services.pack_verification import MAX_PACK_BYTES, verify_pack_bytes

router = APIRouter(prefix="/verify", tags=["verification"])


@router.post("")
def verify_pack(file: UploadFile = File(...)) -> dict:
    if file.content_type not in {"application/zip", "application/x-zip-compressed"}:
        raise HTTPException(status_code=415, detail="Expected a ZIP security pack")
    payload = file.file.read(MAX_PACK_BYTES + 1)
    if len(payload) > MAX_PACK_BYTES:
        raise HTTPException(status_code=413, detail="Security pack exceeds the 20 MB limit")
    return verify_pack_bytes(payload).to_dict()
