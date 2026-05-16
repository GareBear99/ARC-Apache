#!/usr/bin/env python3
"""Smoke tests for ARC-Apache CLI v4. No pytest required."""
from __future__ import annotations
import json, shutil, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "arc_apache.py"

def run(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(CLI), *args], cwd=str(cwd), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

def main() -> int:
    td = Path(tempfile.mkdtemp(prefix="arc_apache_test_"))
    try:
        sample = td / "sample.bin"
        original = b"ARC-Apache binary memory smoke test\n" * 2000
        sample.write_bytes(original)
        store = td / ".arc_apache"
        out = run("pack", str(sample), "--store", str(store), "--content-class", "runtime_event", "--codec", "raw", "--chunk-size", "4096", cwd=ROOT)
        result = json.loads(out.stdout)
        manifest = Path(result["manifest_path"])
        run("verify", str(manifest), "--store", str(store), cwd=ROOT)
        restored = td / "restored.bin"
        run("restore", str(manifest), str(restored), "--store", str(store), cwd=ROOT)
        assert restored.read_bytes() == original
        receipt = run("receipt", str(manifest), "--store", str(store), "--source", "smoke-test", cwd=ROOT)
        assert json.loads(receipt.stdout)["receipt_sha256"]
        params = td / "params.json"
        params.write_text('{"scale":"demo","cells":128}', encoding="utf-8")
        run("sure-recipe", "--generator", "sure-demo", "--seed", "abc123", "--params", str(params), "--store", str(store), cwd=ROOT)
        print("ARC-Apache v4 smoke test passed")
        return 0
    finally:
        shutil.rmtree(td, ignore_errors=True)

if __name__ == "__main__":
    raise SystemExit(main())
