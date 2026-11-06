#!/usr/bin/env python3
"""Regenerate MANIFEST.sha256.json for the current repo tree.

The manifest is the repo's own integrity record: a sorted map of
relative path -> sha256 for every tracked source file. It excludes
itself, .git, caches, virtualenvs, and any ARC-Apache store/key
artifacts (those are secrets, never committed).

Run from the repo root after changing files:
    python scripts/regen_manifest.py
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "MANIFEST.sha256.json"

EXCLUDED_DIRS = {".git", "__pycache__", ".venv", "venv", ".pytest_cache"}
EXCLUDED_FILES = {"MANIFEST.sha256.json"}


def main() -> int:
    entries: dict[str, str] = {}
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT)
        if any(part in EXCLUDED_DIRS for part in rel.parts):
            continue
        if rel.name in EXCLUDED_FILES:
            continue
        # Never hash a store or a key artifact.
        if rel.suffix in {".key.b64"} or "keys/private" in rel.parts:
            continue
        entries[str(rel)] = hashlib.sha256(path.read_bytes()).hexdigest()
    MANIFEST.write_text(
        json.dumps(entries, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"wrote {MANIFEST} ({len(entries)} entries)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
