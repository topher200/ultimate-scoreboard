#!/usr/bin/env python3
"""Build the OTA bundle of the app in src/ for one software version."""

import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.bundle import pack  # noqa: E402


def collect_files(version: str) -> dict[str, bytes]:
    """Return the app files keyed by their path in a slot, with src/version.py set."""
    files = {
        path.relative_to(ROOT_DIR).as_posix(): path.read_bytes()
        for path in sorted((ROOT_DIR / "src").rglob("*.py"))
        if "__pycache__" not in path.parts
    }
    files["src/version.py"] = f'VERSION = "{version}"\n'.encode()
    return files


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version", help="Software version for Memfault, such as 1.2.0")
    parser.add_argument("output", type=Path, help="Path of the bundle to write")
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(pack(collect_files(args.version)))
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
