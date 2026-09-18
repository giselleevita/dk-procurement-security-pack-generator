from __future__ import annotations

import base64
import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone

from app.core.time import isoformat_z, utcnow
from pathlib import Path

from app.crypto.fernet import decrypt_str, encrypt_str


_STATE_FILENAME = "pack_signing_key.json"


def _app_dir() -> Path:
    # backend/app
    return Path(__file__).resolve().parents[1]


def _state_dir() -> Path:
    return _app_dir() / "state"


def _state_path() -> Path:
    return _state_dir() / _STATE_FILENAME


def _b64e(b: bytes) -> str:
    return base64.b64encode(b).decode("ascii")


def _b64d(s: str) -> bytes:
    return base64.b64decode(s.encode("ascii"))


@dataclass(frozen=True)
class SigningMaterial:
    mode: str
    public_key_b64: str

    @property
    def signer_id(self) -> str:
        return hashlib.sha256(self.public_key_b64.encode("ascii")).hexdigest()[:24]

    def sign(self, message: bytes) -> bytes:
        return _load_ed25519_private_key().sign(message)

    def verify(self, message: bytes, signature: bytes) -> bool:
        try:
            _load_ed25519_public_key().verify(signature, message)
            return True
        except Exception:
            return False


class SigningMaterialUnavailable(RuntimeError):
    """Raised when existing signing state cannot be trusted or decrypted."""


def _new_ed25519_payload() -> dict[str, str]:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    private_raw = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_raw = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return {
        "mode": "ed25519",
        "created_at_utc": isoformat_z(utcnow()),
        "public_key_b64": _b64e(public_raw),
        "encrypted_private_key": encrypt_str(_b64e(private_raw)),
    }


def _write_state(payload: dict[str, str]) -> None:
    path = _state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.parent.chmod(0o700)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with tmp.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, sort_keys=True, indent=2)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    tmp.chmod(0o600)
    tmp.replace(path)


def ensure_signing_material() -> SigningMaterial:
    """Create signing material if missing.

    Stored under backend/app/state (gitignored). Private key is encrypted using Fernet.

    Existing state always fails closed. Rotation is an explicit operator action.
    """
    path = _state_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.exists():
        return load_signing_material()

    try:
        _write_state(_new_ed25519_payload())
    except Exception as exc:
        raise SigningMaterialUnavailable("Unable to create Ed25519 signing material") from exc

    return load_signing_material()


def load_signing_material() -> SigningMaterial:
    try:
        obj = json.loads(_state_path().read_text("utf-8"))
        mode = obj.get("mode")
        if mode != "ed25519":
            raise ValueError("only Ed25519 signing material is supported")
        pub = obj.get("public_key_b64")
        enc_priv = obj.get("encrypted_private_key")
        if not pub or not enc_priv:
            raise ValueError("Incomplete signing key material")
        private_raw = _b64d(decrypt_str(enc_priv))
        public_raw = _b64d(pub)
        if len(private_raw) != 32 or len(public_raw) != 32:
            raise ValueError("Invalid Ed25519 key length")
        return SigningMaterial(mode="ed25519", public_key_b64=pub)
    except Exception as exc:
        raise SigningMaterialUnavailable(
            "Signing key state is invalid or cannot be decrypted; run the explicit rotation command"
        ) from exc


def rotate_signing_material() -> SigningMaterial:
    """Explicitly rotate the signer and retain the previous public trust record."""
    path = _state_path()
    if path.exists():
        current = load_signing_material()
        history = _state_dir() / "signing-public-keys"
        history.mkdir(parents=True, exist_ok=True)
        history.chmod(0o700)
        record = {
            "mode": current.mode,
            "public_key_b64": current.public_key_b64,
            "signer_id": current.signer_id,
            "retired_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
        record_path = history / f"{current.signer_id}.json"
        record_path.write_text(json.dumps(record, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        record_path.chmod(0o600)
    _write_state(_new_ed25519_payload())
    return load_signing_material()


def signing_readiness() -> dict[str, str | bool | None]:
    try:
        material = ensure_signing_material()
        return {"ready": True, "mode": material.mode, "signer_id": material.signer_id}
    except SigningMaterialUnavailable:
        return {"ready": False, "mode": None, "signer_id": None}


def canonical_manifest_bytes(manifest: dict) -> bytes:
    # Deterministic JSON bytes (used for signature).
    return (json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _load_ed25519_private_key():
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives import serialization

    obj = json.loads(_state_path().read_text("utf-8"))
    enc_priv = obj["encrypted_private_key"]
    priv_raw = _b64d(decrypt_str(enc_priv))
    return Ed25519PrivateKey.from_private_bytes(priv_raw)


def _load_ed25519_public_key():
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

    obj = json.loads(_state_path().read_text("utf-8"))
    pub_raw = _b64d(obj["public_key_b64"])
    return Ed25519PublicKey.from_public_bytes(pub_raw)
