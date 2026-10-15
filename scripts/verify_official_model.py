"""Verify the frozen official FloodLens AI MultiDomain checkpoint.

Only checks file identity/integrity. It does not grant distribution rights.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

EXPECTED_SHA256 = (
    "82d7be3e54ba74628f7be86334ca10e8f4d4b7327ac224fc7787efde5e1050b3"
)
DEFAULT_MODEL = (
    Path(__file__).resolve().parents[1]
    / "models"
    / "flood_segmentation"
    / "best.pt"
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as model_file:
        while chunk := model_file.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    if len(sys.argv) > 2:
        print("Usage: python scripts/verify_official_model.py [model_path]", file=sys.stderr)
        return 2

    path = Path(sys.argv[1]).expanduser() if len(sys.argv) == 2 else DEFAULT_MODEL
    if not path.is_file():
        print(f"ERROR: Official checkpoint not found: {path}", file=sys.stderr)
        return 2

    actual = sha256_file(path)
    print(f"Model:    {path.resolve()}")
    print(f"SHA-256:  {actual.upper()}")
    print(f"Expected: {EXPECTED_SHA256.upper()}")

    if actual != EXPECTED_SHA256:
        print("FAIL: Checkpoint differs from the frozen official MultiDomain model.")
        return 1

    print("PASS: This is the frozen official MultiDomain checkpoint.")
    print("Note: A checksum match does not establish permission to redistribute weights.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
