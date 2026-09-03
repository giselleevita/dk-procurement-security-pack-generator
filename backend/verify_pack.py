"""Offline verifier for exported DK security packs."""

import argparse
import json
from pathlib import Path

from app.services.pack_verification import verify_pack_bytes


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify hashes and Ed25519 signature in a security pack")
    parser.add_argument("pack", type=Path)
    args = parser.parse_args()
    result = verify_pack_bytes(args.pack.read_bytes())
    print(json.dumps(result.to_dict(), indent=2))
    return 0 if result.valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
