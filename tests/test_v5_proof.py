"""v5 proof-plane tests: tampering must fail, and the v5 manifest format
must stay byte-stable for the same input.

The format test pins the deterministic, content-derived fields of a
manifest produced from a fixed payload. `created_utc` and
`manifest_sha256` are deliberately NOT pinned (they depend on the pack
time and on `source_path`), but every content-derived hash is — so any
change to the v5 envelope, chunking, or Merkle construction fails here.
ARC-Emulator adopts this v5 format as-is; this test is the guard.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "arc_apache.py"

# Fixed payload + parameters used for the v5 format pin. These constants
# were captured from a v5 pack of the same input before the test was added.
BASELINE_PAYLOAD = b"arc apache baseline payload\n"
BASELINE_ENVELOPE_SHA256 = "0f2cdabd2d2e7ad2dab17e2d08cfd39b17fc21caa6b8417dd7c009e3bdf02c78"
BASELINE_MERKLE_ROOT = "1cbc25ac82a9b3041cd8b39a774bd20c053e2a6e418c4e30cf1762993eaf1843"
BASELINE_OBJECT_ID = "arcbin:0f2cdabd2d2e7ad2dab17e2d08cfd39b17fc21caa6b8417dd7c009e3bdf02c78"
BASELINE_ENVELOPE_SIZE = 249
BASELINE_CHUNK_HASHES = [
    "7913b3aad2009eaa03999bf1ed3eab2b2113ee3d77422325e7ec34dc0bb79859",
    "5da400305b91652c8038822645af15498e4d650d71a7b5d61105be1c0892c565",
    "ccaebf1f10f82c763119f1dc407aa3de74b63777b353ba710ba972f2a3be79c0",
    "f77962929210c8b290d33acfb0f44d3185c0b23fb13eae3f5041747a5bcf2b57",
    "46a24813001972656fe8f38b91df8be97e50df46a037aa4c626fa7d53aba66a2",
    "9d711186d772dd0ac96a783cec77c6381d9fcc2c798af576a8c59c2c08df12eb",
    "6519f7e2f7278aabe8b796e5f792ab73849fe96f47462e320b6342035c755a06",
    "3fb118eafbe3c91459ac8cc27bee725ed198039bc8ba6d1ed25cdb3cda6dc8d5",
    "e3f0c5e434dc46e3f244b37a6a15c7f9a4aeceb7c711a9b286810ccc10548ab4",
    "6a88864a32267134cf51c877556571066535c7d5070d83b394657ba79ca27e1a",
    "c550673058bdf50e9048b796b5da898b96e68bd28c69d45c368d273a7a7b254f",
    "6bb4313917765a03d2c9a1259a4c3a545c866da9cdfd6fe6d043822a4bee041f",
    "c223300dcff470613139be5cf4cdd388e975635b9aafe51798236a5984f03ad7",
    "820acd1422ace5312929178f768b36cfa4a498d535e0916091b28e6351ae197c",
    "e850f1ce3c316c3d4783dde7d42073bb76dd89c8e3d71e2ef7cf452b3c41db36",
    "50f868dd95f5c309f83119e5444f1ab8009c0a9651e356cf2c0ff5fab6432f19",
]
EXPECTED_MANIFEST_KEYS = {
    "chunk_size", "chunks", "codec", "content_class", "created_utc",
    "envelope_sha256", "envelope_size_bytes", "manifest_sha256",
    "merkle_root", "object_id", "parents", "source_path", "version",
}
HEX64 = re.compile(r"^[a-f0-9]{64}$")


def run_cli(*args, cwd=None):
    return subprocess.run(
        [sys.executable, str(CLI), *args], cwd=cwd or ROOT,
        text=True, capture_output=True,
    )


def run_ok(*args, cwd=None):
    proc = run_cli(*args, cwd=cwd)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def pack_sample(tmp_path, chunk_size=16):
    store = tmp_path / "store"
    sample = tmp_path / "sample.txt"
    sample.write_text("hello arc apache\n", encoding="utf-8")
    run_ok("init-store", "--store", str(store))
    packed = run_ok(
        "pack", str(sample), "--store", str(store),
        "--content-class", "test", "--codec", "utf8-text",
        "--chunk-size", str(chunk_size),
    )
    return store, Path(packed["manifest_path"])


def test_verify_fails_on_tampered_chunk(tmp_path):
    store, manifest_path = pack_sample(tmp_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    chunk_path = store / manifest["chunks"][0]["store_path"]
    data = bytearray(chunk_path.read_bytes())
    data[0] ^= 0xFF
    chunk_path.write_bytes(bytes(data))
    proc = run_cli("verify", str(manifest_path), "--store", str(store))
    assert proc.returncode == 2
    result = json.loads(proc.stdout)
    assert result["ok"] is False
    assert result["errors"]


def test_verify_fails_on_missing_chunk(tmp_path):
    store, manifest_path = pack_sample(tmp_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    (store / manifest["chunks"][0]["store_path"]).unlink()
    proc = run_cli("verify", str(manifest_path), "--store", str(store))
    assert proc.returncode == 2
    result = json.loads(proc.stdout)
    assert result["ok"] is False
    assert any("missing chunk" in e for e in result["errors"])


def test_restore_fails_on_tampered_manifest(tmp_path):
    store, manifest_path = pack_sample(tmp_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    chunk_path = store / manifest["chunks"][0]["store_path"]
    data = bytearray(chunk_path.read_bytes())
    data[0] ^= 0xFF
    chunk_path.write_bytes(bytes(data))
    proc = run_cli(
        "restore", str(manifest_path), str(tmp_path / "out.txt"),
        "--store", str(store),
    )
    assert proc.returncode == 2


def test_v5_manifest_format_is_stable(tmp_path):
    """The deterministic v5 fields for a fixed payload must not change."""
    store = tmp_path / "store"
    sample = tmp_path / "input.txt"
    sample.write_bytes(BASELINE_PAYLOAD)
    run_ok("init-store", "--store", str(store))
    packed = run_ok(
        "pack", str(sample), "--store", str(store),
        "--content-class", "baseline", "--codec", "utf8-text",
        "--chunk-size", "16",
    )
    manifest = json.loads(Path(packed["manifest_path"]).read_text(encoding="utf-8"))
    assert set(manifest.keys()) == EXPECTED_MANIFEST_KEYS
    assert manifest["version"] == 5
    assert manifest["content_class"] == "baseline"
    assert manifest["codec"] == "utf8-text"
    assert manifest["envelope_sha256"] == BASELINE_ENVELOPE_SHA256
    assert manifest["envelope_size_bytes"] == BASELINE_ENVELOPE_SIZE
    assert manifest["object_id"] == BASELINE_OBJECT_ID
    assert manifest["merkle_root"] == BASELINE_MERKLE_ROOT
    assert manifest["chunk_size"] == 16
    assert len(manifest["chunks"]) == 16
    assert [c["sha256"] for c in manifest["chunks"]] == BASELINE_CHUNK_HASHES
    assert [c["size_bytes"] for c in manifest["chunks"]] == [16] * 15 + [9]
    assert [c["index"] for c in manifest["chunks"]] == list(range(16))
    # Schema-shape check (mirrors schemas/binary_manifest.schema.json).
    assert HEX64.match(manifest["manifest_sha256"])
    assert HEX64.match(manifest["envelope_sha256"])
    assert HEX64.match(manifest["merkle_root"])
    assert manifest["object_id"].startswith("arcbin:")
    for chunk in manifest["chunks"]:
        assert set(chunk.keys()) == {"index", "sha256", "size_bytes", "store_path"}
        assert HEX64.match(chunk["sha256"])
    # And the manifest still verifies (hash chain intact).
    verified = run_ok("verify", str(packed["manifest_path"]), "--store", str(store))
    assert verified["ok"] is True


def test_receipt_sign_verify_round_trip(tmp_path):
    pytest.importorskip("cryptography")
    store, manifest_path = pack_sample(tmp_path)
    run_ok("keygen", "--store", str(store), "--name", "local-node")
    receipt = run_ok(
        "receipt", str(manifest_path), "--store", str(store), "--source", "test",
    )
    receipt_path = Path(receipt["receipt_path"])
    # Unsigned receipts do not verify.
    proc = run_cli("verify-receipt", str(receipt_path), "--store", str(store))
    assert proc.returncode == 2
    assert json.loads(proc.stdout)["ok"] is False
    # Signed receipts do.
    run_ok("sign-receipt", str(receipt_path), "--store", str(store), "--key-name", "local-node")
    verified = run_ok("verify-receipt", str(receipt_path), "--store", str(store))
    assert verified["ok"] is True
