import base64
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "arc_apache.py"


def run(*args, cwd=None):
    return subprocess.run([sys.executable, str(CLI), *args], cwd=cwd or ROOT, text=True, capture_output=True, check=True)


def test_pack_verify_restore_receipt(tmp_path):
    store = tmp_path / "store"
    sample = tmp_path / "sample.txt"
    sample.write_text("hello arc apache\n", encoding="utf-8")
    run("init-store", "--store", str(store))
    packed = json.loads(run("pack", str(sample), "--store", str(store), "--content-class", "test", "--codec", "utf8-text", "--chunk-size", "16").stdout)
    manifest = Path(packed["manifest_path"])
    verified = json.loads(run("verify", str(manifest), "--store", str(store)).stdout)
    assert verified["ok"] is True
    out = tmp_path / "restored.txt"
    restored = json.loads(run("restore", str(manifest), str(out), "--store", str(store)).stdout)
    assert restored["ok"] is True
    assert out.read_text(encoding="utf-8") == "hello arc apache\n"
    receipt = json.loads(run("receipt", str(manifest), "--store", str(store), "--source", "test").stdout)
    assert len(receipt["receipt_sha256"]) == 64


def test_stream_manifest(tmp_path):
    frames = tmp_path / "frames"
    frames.mkdir()
    (frames / "0001.bin").write_bytes(b"frame1")
    (frames / "0002.bin").write_bytes(b"frame2")
    store = tmp_path / "store"
    out = tmp_path / "stream.json"
    result = json.loads(run("stream-manifest", str(frames), "--stream-id", "test-stream", "--store", str(store), "--out", str(out)).stdout)
    assert result["ok"] is True
    seq = json.loads(out.read_text(encoding="utf-8"))
    assert len(seq["frames"]) == 2
    assert len(seq["sequence_sha256"]) == 64


def test_smoke(tmp_path):
    result = json.loads(run("smoke", "--store", str(tmp_path / "smoke_store")).stdout)
    assert result["ok"] is True
