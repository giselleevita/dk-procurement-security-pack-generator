from __future__ import annotations

import base64
import hashlib
import json
from dataclasses import dataclass, field
from io import BytesIO
from zipfile import BadZipFile, ZipFile

MAX_PACK_BYTES = 20_000_000
EXPECTED_FILES = {"report.md", "report.pdf", "evidence-pack.zip", "pack_manifest.json", "pack_manifest.sig"}


@dataclass(frozen=True)
class VerificationResult:
    valid: bool
    signature_valid: bool
    hashes_valid: bool
    schema_version: str | None = None
    signer_id: str | None = None
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "valid": self.valid,
            "signature_valid": self.signature_valid,
            "hashes_valid": self.hashes_valid,
            "schema_version": self.schema_version,
            "signer_id": self.signer_id,
            "errors": self.errors,
        }


def verify_pack_bytes(payload: bytes) -> VerificationResult:
    if len(payload) > MAX_PACK_BYTES:
        return VerificationResult(False, False, False, errors=["pack exceeds size limit"])
    errors: list[str] = []
    try:
        with ZipFile(BytesIO(payload)) as archive:
            names = set(archive.namelist())
            if not EXPECTED_FILES.issubset(names):
                return VerificationResult(False, False, False, errors=["pack is missing required files"])
            manifest_bytes = archive.read("pack_manifest.json")
            manifest = json.loads(manifest_bytes)
            if manifest.get("schema_version") != "pack/v1":
                errors.append("unsupported manifest schema")
            hashes_valid = True
            for name, expected in manifest.get("hashes", {}).items():
                if name not in EXPECTED_FILES or name.startswith("pack_manifest"):
                    errors.append(f"invalid manifest entry: {name}")
                    hashes_valid = False
                    continue
                actual = hashlib.sha256(archive.read(name)).hexdigest()
                if actual != expected:
                    errors.append(f"hash mismatch: {name}")
                    hashes_valid = False
            signature_valid = False
            if manifest.get("mode") != "ed25519" or not manifest.get("public_key_b64"):
                errors.append("pack does not contain an independently verifiable Ed25519 key")
            else:
                from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

                try:
                    key = Ed25519PublicKey.from_public_bytes(base64.b64decode(manifest["public_key_b64"]))
                    signature = base64.b64decode(archive.read("pack_manifest.sig").strip(), validate=True)
                    key.verify(signature, manifest_bytes)
                    signature_valid = True
                except Exception:
                    errors.append("signature verification failed")
            valid = hashes_valid and signature_valid and not errors
            return VerificationResult(
                valid, signature_valid, hashes_valid,
                schema_version=manifest.get("schema_version"), signer_id=manifest.get("signer_id"), errors=errors,
            )
    except (BadZipFile, KeyError, json.JSONDecodeError, ValueError):
        return VerificationResult(False, False, False, errors=["invalid security-pack archive"])
