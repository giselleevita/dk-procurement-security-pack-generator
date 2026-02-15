from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from datetime import datetime

from app.core.time import isoformat_z, utcnow
from pathlib import Path

from app.core.settings import get_settings
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
    mode: str  # ed25519|hmac
    public_key_b64: str | None

    def sign(self, message: bytes) -> bytes:
        if self.mode == "ed25519":
            priv = _load_ed25519_private_key()
            return priv.sign(message)
        if self.mode == "hmac":
            import hmac
            import hashlib

            key = _hmac_key_from_fernet()
            return hmac.new(key, message, hashlib.sha256).digest()
        raise ValueError("Unknown signing mode")

    def verify(self, message: bytes, signature: bytes) -> bool:
        if self.mode == "ed25519":
            pub = _load_ed25519_public_key()
            try:
                pub.verify(signature, message)
                return True
            except Exception:
                return False
        if self.mode == "hmac":
            import hmac
            import hashlib

            key = _hmac_key_from_fernet()
            expected = hmac.new(key, message, hashlib.sha256).digest()
            return hmac.compare_digest(expected, signature)
        return False


def ensure_signing_material() -> SigningMaterial:
    """Create signing material if missing.

    Stored under backend/app/state (gitignored). Private key is encrypted using Fernet.

    Failure mode: if the Fernet key changes and the private key cannot be decrypted,
    a new signing key is generated (older packs may no longer verify against this
    instance's trust anchor).
    """
    path = _state_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.exists():
        try:
            return load_signing_material()
        except Exception:
            # Corrupt or undecryptable -> rotate.
            pass

    # Prefer Ed25519 when available.
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        from cryptography.hazmat.primitives import serialization

        priv = Ed25519PrivateKey.generate()
        pub = priv.public_key()

        priv_raw = priv.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption(),
        )
        pub_raw = pub.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )

        payload = {
            "mode": "ed25519",
            "created_at_utc": isoformat_z(utcnow()),
            "public_key_b64": _b64e(pub_raw),
            "encrypted_private_key": encrypt_str(_b64e(priv_raw)),
        }
    except Exception:
        # Fallback: HMAC based on Fernet key.
        payload = {
            "mode": "hmac",
            "created_at_utc": isoformat_z(utcnow()),
        }

    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    try:
        tmp.chmod(0o600)
    except Exception:
        pass
    tmp.replace(path)

    return load_signing_material()


def load_signing_material() -> SigningMaterial:
    obj = json.loads(_state_path().read_text("utf-8"))
    mode = obj.get("mode")
    if mode == "ed25519":
        pub = obj.get("public_key_b64")
        enc_priv = obj.get("encrypted_private_key")
        if not pub or not enc_priv:
            raise ValueError("Incomplete signing key material")
        # Verify decryptability now (so we rotate early if Fernet changed).
        _ = decrypt_str(enc_priv)
        return SigningMaterial(mode="ed25519", public_key_b64=pub)
    if mode == "hmac":
        return SigningMaterial(mode="hmac", public_key_b64=None)
    raise ValueError("Unknown signing mode")


def canonical_manifest_bytes(manifest: dict) -> bytes:
    # Deterministic JSON bytes (used for signature).
    return (json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _hmac_key_from_fernet() -> bytes:
    import hashlib

    settings = get_settings()
    # Derive a dedicated MAC key from the Fernet key material.
    return hashlib.sha256(("dkpack-export-mac:" + settings.fernet_key).encode("utf-8")).digest()


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
