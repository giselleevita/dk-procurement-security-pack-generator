from __future__ import annotations

import argparse

from app.services.pack_signing import rotate_signing_material


def main() -> int:
    parser = argparse.ArgumentParser(description="Rotate the security-pack Ed25519 signing key")
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Acknowledge that subsequent packs will use a new signer ID",
    )
    args = parser.parse_args()
    if not args.confirm:
        parser.error("--confirm is required")
    material = rotate_signing_material()
    print(f"Rotated Ed25519 signing key; signer_id={material.signer_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
