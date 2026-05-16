#!/usr/bin/env python3
"""ARC-Apache v5 binary-first cryptographic memory CLI.

Core path is dependency-free. Optional signing/encryption uses cryptography.
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import json
import os
import shutil
import struct
import sys
import tempfile
from pathlib import Path
from typing import Any

MAGIC = b"ARC_APACHE_BIN\0"
VERSION = 5
DEFAULT_CHUNK_SIZE = 1024 * 1024

LANGUAGE_TARGETS = [
    "data/arc_language.db",
    "arc_language.db",
    "config/common_languages_seed.json",
    "config/common_phrases_seed.json",
    "config/common_etymologies_seed.json",
    "config/concepts_seed.json",
    "config/phonology_seed.json",
    "config/pronunciation_seed.json",
    "config/transliteration_seed.json",
    "config/variants_seed.json",
    "config/corpus_manifests.json",
    "config/source_manifests.json",
    "config/backend_manifests.json",
]


def utc_now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json_bytes(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def b64e(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def b64d(text: str) -> bytes:
    return base64.b64decode(text.encode("ascii"))


def merkle_root(hex_hashes: list[str]) -> str:
    if not hex_hashes:
        return sha256_bytes(b"")
    level = [bytes.fromhex(h) for h in hex_hashes]
    while len(level) > 1:
        if len(level) % 2:
            level.append(level[-1])
        level = [hashlib.sha256(level[i] + level[i + 1]).digest() for i in range(0, len(level), 2)]
    return level[0].hex()


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(delete=False, dir=str(path.parent)) as f:
        tmp = Path(f.name)
        f.write(data)
    os.replace(tmp, path)


def write_json(path: Path, obj: Any) -> None:
    atomic_write(path, (json.dumps(obj, indent=2, sort_keys=True) + "\n").encode("utf-8"))


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_store(store: Path) -> None:
    for rel in ["objects/sha256", "manifests", "receipts", "keys/public", "keys/private", "streams", "bundles", "indexes", "tmp"]:
        (store / rel).mkdir(parents=True, exist_ok=True)
    meta = store / "STORE.json"
    if not meta.exists():
        write_json(meta, {"store_version": VERSION, "created_utc": utc_now(), "doctrine": "binary-first cryptographic ARC memory store"})


def make_envelope(payload: bytes, *, content_class: str, codec: str, encryption: dict[str, Any] | None = None) -> bytes:
    meta = {"version": VERSION, "content_class": content_class, "codec": codec, "encryption": encryption, "payload_sha256": sha256_bytes(payload)}
    mb = canonical_json_bytes(meta)
    # MAGIC + metadata length + payload length + metadata + payload + footer(payload hash bytes)
    return MAGIC + struct.pack(">IQ", len(mb), len(payload)) + mb + payload + hashlib.sha256(payload).digest()


def parse_envelope(envelope: bytes) -> dict[str, Any]:
    if not envelope.startswith(MAGIC):
        raise ValueError("not an ARC-Apache binary envelope")
    off = len(MAGIC)
    meta_len, payload_len = struct.unpack(">IQ", envelope[off:off + 12])
    off += 12
    meta = json.loads(envelope[off:off + meta_len].decode("utf-8"))
    off += meta_len
    payload = envelope[off:off + payload_len]
    off += payload_len
    footer = envelope[off:off + 32]
    if len(footer) != 32:
        raise ValueError("missing envelope footer")
    if hashlib.sha256(payload).digest() != footer:
        raise ValueError("envelope footer hash mismatch")
    if meta.get("payload_sha256") != sha256_bytes(payload):
        raise ValueError("metadata payload hash mismatch")
    return {"metadata": meta, "payload": payload}


def store_chunk(store: Path, chunk: bytes) -> tuple[str, str]:
    h = sha256_bytes(chunk)
    rel = Path("objects") / "sha256" / h[:2] / h[2:4] / f"{h}.bin"
    out = store / rel
    if not out.exists():
        atomic_write(out, chunk)
    return h, str(rel)


def pack_bytes(data: bytes, *, store: Path, content_class: str, codec: str, source_path: str | None, chunk_size: int, parents: list[str] | None = None, extra: dict[str, Any] | None = None, encryption: dict[str, Any] | None = None) -> dict[str, Any]:
    ensure_store(store)
    envelope = make_envelope(data, content_class=content_class, codec=codec, encryption=encryption)
    payload_hash = sha256_bytes(envelope)
    chunks: list[dict[str, Any]] = []
    chunk_hashes: list[str] = []
    for idx in range(0, len(envelope), chunk_size):
        chunk = envelope[idx:idx + chunk_size]
        h, rel = store_chunk(store, chunk)
        chunk_hashes.append(h)
        chunks.append({"index": len(chunks), "sha256": h, "size_bytes": len(chunk), "store_path": rel})
    manifest: dict[str, Any] = {
        "version": VERSION,
        "object_id": f"arcbin:{payload_hash}",
        "content_class": content_class,
        "codec": codec,
        "envelope_sha256": payload_hash,
        "envelope_size_bytes": len(envelope),
        "chunk_size": chunk_size,
        "chunks": chunks,
        "merkle_root": merkle_root(chunk_hashes),
        "source_path": source_path,
        "parents": parents or [],
        "created_utc": utc_now(),
    }
    if encryption:
        manifest["encryption"] = {k: v for k, v in encryption.items() if k != "key_material_b64"}
    if extra:
        manifest["extra"] = extra
    unsigned = dict(manifest)
    unsigned["manifest_sha256"] = None
    manifest["manifest_sha256"] = sha256_bytes(canonical_json_bytes(unsigned))
    write_json(store / "manifests" / f"{manifest['manifest_sha256']}.json", manifest)
    return manifest


def rebuild_envelope(manifest: dict[str, Any], store: Path) -> bytes:
    return b"".join((store / ch["store_path"]).read_bytes() for ch in sorted(manifest["chunks"], key=lambda x: x["index"]))


def verify_manifest(manifest: dict[str, Any], store: Path) -> tuple[bool, list[str]]:
    errors: list[str] = []
    rebuilt = bytearray()
    chunk_hashes: list[str] = []
    for ch in sorted(manifest.get("chunks", []), key=lambda x: x["index"]):
        p = store / ch["store_path"]
        if not p.exists():
            errors.append(f"missing chunk: {p}")
            continue
        data = p.read_bytes()
        h = sha256_bytes(data)
        chunk_hashes.append(h)
        rebuilt.extend(data)
        if h != ch["sha256"]:
            errors.append(f"chunk sha256 mismatch: {p}")
        if len(data) != ch["size_bytes"]:
            errors.append(f"chunk size mismatch: {p}")
    if sha256_bytes(bytes(rebuilt)) != manifest.get("envelope_sha256"):
        errors.append("envelope_sha256 mismatch")
    if merkle_root(chunk_hashes) != manifest.get("merkle_root"):
        errors.append("merkle_root mismatch")
    unsigned = dict(manifest)
    expected = unsigned.pop("manifest_sha256", None)
    unsigned["manifest_sha256"] = None
    actual = sha256_bytes(canonical_json_bytes(unsigned))
    if actual != expected:
        errors.append("manifest_sha256 mismatch")
    try:
        parse_envelope(bytes(rebuilt))
    except Exception as e:
        errors.append(f"envelope parse failed: {e}")
    return not errors, errors


def load_private_key(store: Path, key_name: str):
    try:
        from cryptography.hazmat.primitives import serialization
    except Exception as e:
        raise RuntimeError("cryptography is required for signing/encryption") from e
    p = store / "keys" / "private" / f"{key_name}.ed25519.pem"
    if not p.exists():
        raise FileNotFoundError(f"missing private key: {p}")
    return serialization.load_pem_private_key(p.read_bytes(), password=None)


def load_public_key(store: Path, key_name: str):
    try:
        from cryptography.hazmat.primitives import serialization
    except Exception as e:
        raise RuntimeError("cryptography is required for signature verification") from e
    p = store / "keys" / "public" / f"{key_name}.ed25519.pub.pem"
    if not p.exists():
        raise FileNotFoundError(f"missing public key: {p}")
    return serialization.load_pem_public_key(p.read_bytes())


def aes_gcm_encrypt(data: bytes) -> tuple[bytes, dict[str, Any], bytes]:
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    except Exception as e:
        raise RuntimeError("cryptography is required for AES-GCM encryption") from e
    key = AESGCM.generate_key(bit_length=256)
    nonce = os.urandom(12)
    aes = AESGCM(key)
    aad = b"ARC-Apache-v5"
    ciphertext = aes.encrypt(nonce, data, aad)
    enc = {"algorithm": "AES-256-GCM", "nonce_b64": b64e(nonce), "aad_b64": b64e(aad), "key_sha256": sha256_bytes(key)}
    return ciphertext, enc, key


def aes_gcm_decrypt(data: bytes, enc: dict[str, Any], key: bytes) -> bytes:
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    except Exception as e:
        raise RuntimeError("cryptography is required for AES-GCM decryption") from e
    if sha256_bytes(key) != enc.get("key_sha256"):
        raise ValueError("decryption key hash mismatch")
    return AESGCM(key).decrypt(b64d(enc["nonce_b64"]), data, b64d(enc["aad_b64"]))


def cmd_init_store(args: argparse.Namespace) -> int:
    ensure_store(Path(args.store))
    print(json.dumps({"ok": True, "store": args.store}, indent=2))
    return 0


def cmd_keygen(args: argparse.Namespace) -> int:
    ensure_store(Path(args.store))
    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    except Exception as e:
        print(json.dumps({"ok": False, "error": "cryptography package required for keygen", "detail": str(e)}, indent=2), file=sys.stderr)
        return 2
    key = Ed25519PrivateKey.generate()
    priv = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
    pub = key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
    priv_path = Path(args.store) / "keys" / "private" / f"{args.name}.ed25519.pem"
    pub_path = Path(args.store) / "keys" / "public" / f"{args.name}.ed25519.pub.pem"
    if priv_path.exists() and not args.force:
        print(json.dumps({"ok": False, "error": "key exists; pass --force to replace", "key_name": args.name}, indent=2), file=sys.stderr)
        return 2
    atomic_write(priv_path, priv)
    atomic_write(pub_path, pub)
    os.chmod(priv_path, 0o600)
    print(json.dumps({"ok": True, "key_name": args.name, "public_key_path": str(pub_path), "private_key_path": str(priv_path)}, indent=2))
    return 0


def cmd_pack(args: argparse.Namespace) -> int:
    data = Path(args.input).read_bytes()
    key_out = None
    enc_meta = None
    codec = args.codec
    if args.encrypt:
        data, enc_meta, key = aes_gcm_encrypt(data)
        codec = f"encrypted:{codec}"
        key_out = Path(args.key_out or (str(Path(args.input).name) + ".aesgcm.key.b64"))
        atomic_write(key_out, b64e(key).encode("ascii") + b"\n")
    manifest = pack_bytes(data, store=Path(args.store), content_class=args.content_class, codec=codec, source_path=str(Path(args.input)), chunk_size=args.chunk_size, parents=args.parent or [], encryption=enc_meta)
    out = {"ok": True, "manifest_sha256": manifest["manifest_sha256"], "envelope_sha256": manifest["envelope_sha256"], "merkle_root": manifest["merkle_root"], "chunks": len(manifest["chunks"]), "manifest_path": str(Path(args.store) / "manifests" / f"{manifest['manifest_sha256']}.json")}
    if key_out:
        out["decryption_key_path"] = str(key_out)
    print(json.dumps(out, indent=2))
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    manifest = read_json(Path(args.manifest))
    ok, errors = verify_manifest(manifest, Path(args.store))
    print(json.dumps({"ok": ok, "errors": errors, "manifest_sha256": manifest.get("manifest_sha256")}, indent=2))
    return 0 if ok else 2


def cmd_restore(args: argparse.Namespace) -> int:
    store = Path(args.store)
    manifest = read_json(Path(args.manifest))
    ok, errors = verify_manifest(manifest, store)
    if not ok:
        print(json.dumps({"ok": False, "errors": errors}, indent=2), file=sys.stderr)
        return 2
    parsed = parse_envelope(rebuild_envelope(manifest, store))
    payload = parsed["payload"]
    meta = parsed["metadata"]
    if meta.get("encryption"):
        if not args.key:
            print(json.dumps({"ok": False, "error": "manifest is encrypted; pass --key <base64 key file>"}, indent=2), file=sys.stderr)
            return 2
        key = b64d(Path(args.key).read_text(encoding="utf-8").strip())
        payload = aes_gcm_decrypt(payload, meta["encryption"], key)
    if args.envelope:
        atomic_write(Path(args.output), rebuild_envelope(manifest, store))
    else:
        atomic_write(Path(args.output), payload)
    print(json.dumps({"ok": True, "output": args.output, "wrote_envelope": bool(args.envelope), "content_class": meta.get("content_class"), "codec": meta.get("codec")}, indent=2))
    return 0


def cmd_receipt(args: argparse.Namespace) -> int:
    ensure_store(Path(args.store))
    manifest = read_json(Path(args.manifest))
    receipt = {
        "version": VERSION,
        "receipt_type": args.receipt_type,
        "source": args.source,
        "actor": args.actor,
        "policy_status": args.policy_status,
        "manifest_sha256": manifest["manifest_sha256"],
        "envelope_sha256": manifest["envelope_sha256"],
        "merkle_root": manifest["merkle_root"],
        "content_class": manifest.get("content_class"),
        "parent_receipts": args.parent or [],
        "created_utc": utc_now(),
        "signature": None,
    }
    unsigned = dict(receipt)
    unsigned["receipt_sha256"] = None
    receipt["receipt_sha256"] = sha256_bytes(canonical_json_bytes(unsigned))
    out = Path(args.store) / "receipts" / f"{receipt['receipt_sha256']}.json"
    write_json(out, receipt)
    print(json.dumps({"ok": True, "receipt_sha256": receipt["receipt_sha256"], "receipt_path": str(out)}, indent=2))
    return 0


def cmd_sign_receipt(args: argparse.Namespace) -> int:
    store = Path(args.store)
    receipt_path = Path(args.receipt)
    receipt = read_json(receipt_path)
    sigless = dict(receipt)
    sigless["signature"] = None
    payload = canonical_json_bytes(sigless)
    try:
        key = load_private_key(store, args.key_name)
        sig = key.sign(payload)
    except Exception as e:
        print(json.dumps({"ok": False, "error": str(e)}, indent=2), file=sys.stderr)
        return 2
    receipt["signature"] = {"algorithm": "Ed25519", "key_name": args.key_name, "signature_b64": b64e(sig), "signed_utc": utc_now()}
    write_json(receipt_path, receipt)
    print(json.dumps({"ok": True, "receipt": str(receipt_path), "key_name": args.key_name}, indent=2))
    return 0


def cmd_verify_receipt(args: argparse.Namespace) -> int:
    store = Path(args.store)
    receipt = read_json(Path(args.receipt))
    errors: list[str] = []
    unsigned = dict(receipt)
    expected = unsigned.pop("receipt_sha256", None)
    sig = receipt.get("signature")
    # The receipt hash is the stable receipt identity and deliberately excludes
    # the mutable signature block. Signatures bind to the hash-bearing receipt
    # with signature=None, so receipts can be countersigned without changing ID.
    unsigned["receipt_sha256"] = None
    unsigned["signature"] = None
    actual = sha256_bytes(canonical_json_bytes(unsigned))
    if actual != expected:
        errors.append("receipt_sha256 mismatch")
    if sig:
        sigless = dict(receipt)
        sigless["signature"] = None
        payload = canonical_json_bytes(sigless)
        try:
            pub = load_public_key(store, sig["key_name"])
            pub.verify(b64d(sig["signature_b64"]), payload)
        except Exception as e:
            errors.append(f"signature verification failed: {e}")
    else:
        errors.append("receipt is unsigned")
    ok = not errors
    print(json.dumps({"ok": ok, "errors": errors, "receipt_sha256": expected}, indent=2))
    return 0 if ok else 2


def cmd_mirror_language(args: argparse.Namespace) -> int:
    root = Path(args.language_root)
    report: dict[str, Any] = {"language_root": str(root), "packed": [], "missing": [], "created_utc": utc_now()}
    for rel in LANGUAGE_TARGETS:
        p = root / rel
        if not p.exists():
            report["missing"].append(rel)
            continue
        extra = {"language_link": {"source_relative_path": rel, "module_role": "lexical_meaning_spine", "canonical_surface": "binary_manifest"}}
        manifest = pack_bytes(p.read_bytes(), store=Path(args.store), content_class="language_graph", codec="arc-language-file", source_path=str(p), chunk_size=args.chunk_size, extra=extra)
        report["packed"].append({"source": rel, "manifest_sha256": manifest["manifest_sha256"], "envelope_sha256": manifest["envelope_sha256"], "merkle_root": manifest["merkle_root"]})
    write_json(Path(args.out), report)
    print(json.dumps({"ok": True, "packed": len(report["packed"]), "missing": len(report["missing"]), "report": args.out}, indent=2))
    return 0


def cmd_stream_manifest(args: argparse.Namespace) -> int:
    root = Path(args.frames_dir)
    frames = sorted([p for p in root.iterdir() if p.is_file()])
    seq: dict[str, Any] = {"version": VERSION, "stream_id": args.stream_id, "source": args.source, "frames": [], "created_utc": utc_now()}
    for i, frame in enumerate(frames):
        manifest = pack_bytes(frame.read_bytes(), store=Path(args.store), content_class="stream_frame", codec=args.codec, source_path=str(frame), chunk_size=args.chunk_size, extra={"stream_id": args.stream_id, "frame_index": i})
        seq["frames"].append({"index": i, "source_path": str(frame), "manifest_sha256": manifest["manifest_sha256"], "envelope_sha256": manifest["envelope_sha256"], "merkle_root": manifest["merkle_root"]})
    seq["sequence_sha256"] = sha256_bytes(canonical_json_bytes({k: v for k, v in seq.items() if k != "sequence_sha256"}))
    out = Path(args.out or (Path(args.store) / "streams" / f"{args.stream_id}.stream.json"))
    write_json(out, seq)
    print(json.dumps({"ok": True, "stream_id": args.stream_id, "frames": len(frames), "sequence_sha256": seq["sequence_sha256"], "stream_manifest": str(out)}, indent=2))
    return 0


def cmd_sure_recipe(args: argparse.Namespace) -> int:
    params = read_json(Path(args.params)) if args.params else {}
    recipe = {
        "version": VERSION,
        "generator_id": args.generator,
        "generator_version": args.generator_version,
        "seed": args.seed,
        "parameters_sha256": sha256_bytes(canonical_json_bytes(params)),
        "parameters": params,
        "environment_fingerprint": args.environment,
        "expected_output_sha256": args.expected_output_sha256,
        "notes": args.notes,
        "created_utc": utc_now(),
    }
    manifest = pack_bytes(canonical_json_bytes(recipe), store=Path(args.store), content_class="sure_seed_recipe", codec="arc-json-canonical", source_path=args.params, chunk_size=args.chunk_size, extra={"sure_recipe": {k: v for k, v in recipe.items() if k != "parameters"}})
    print(json.dumps({"ok": True, "manifest_sha256": manifest["manifest_sha256"], "envelope_sha256": manifest["envelope_sha256"], "parameters_sha256": recipe["parameters_sha256"]}, indent=2))
    return 0


def cmd_bundle_plan(args: argparse.Namespace) -> int:
    manifests = [read_json(Path(p)) for p in args.manifest]
    receipts = [read_json(Path(p)) for p in (args.receipt or [])]
    plan = {
        "version": VERSION,
        "bundle_type": "arc-rar-proof-plan",
        "name": args.name,
        "manifests": [{"manifest_sha256": m["manifest_sha256"], "envelope_sha256": m["envelope_sha256"], "merkle_root": m["merkle_root"], "chunks": len(m["chunks"])} for m in manifests],
        "receipts": [{"receipt_sha256": r.get("receipt_sha256"), "manifest_sha256": r.get("manifest_sha256"), "signed": bool(r.get("signature"))} for r in receipts],
        "created_utc": utc_now(),
    }
    plan["bundle_plan_sha256"] = sha256_bytes(canonical_json_bytes({k: v for k, v in plan.items() if k != "bundle_plan_sha256"}))
    write_json(Path(args.out), plan)
    print(json.dumps({"ok": True, "bundle_plan_sha256": plan["bundle_plan_sha256"], "out": args.out}, indent=2))
    return 0


def cmd_smoke(args: argparse.Namespace) -> int:
    store = Path(args.store)
    if store.exists():
        shutil.rmtree(store)
    ensure_store(store)
    sample = store / "tmp" / "sample.txt"
    sample.parent.mkdir(parents=True, exist_ok=True)
    sample.write_text("arc apache smoke\n", encoding="utf-8")
    manifest = pack_bytes(sample.read_bytes(), store=store, content_class="smoke", codec="utf8-text", source_path=str(sample), chunk_size=64)
    ok, errors = verify_manifest(manifest, store)
    if not ok:
        print(json.dumps({"ok": False, "stage": "verify", "errors": errors}, indent=2), file=sys.stderr)
        return 2
    out = store / "tmp" / "restored.txt"
    parsed = parse_envelope(rebuild_envelope(manifest, store))
    out.write_bytes(parsed["payload"])
    if out.read_bytes() != sample.read_bytes():
        print(json.dumps({"ok": False, "stage": "restore"}, indent=2), file=sys.stderr)
        return 2
    print(json.dumps({"ok": True, "message": "ARC-Apache v5 smoke test passed", "manifest_sha256": manifest["manifest_sha256"]}, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="arc-apache", description="ARC-Apache v5 binary-first cryptographic memory CLI")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init-store"); p.add_argument("--store", default=".arc_apache"); p.set_defaults(func=cmd_init_store)
    p = sub.add_parser("keygen"); p.add_argument("--store", default=".arc_apache"); p.add_argument("--name", required=True); p.add_argument("--force", action="store_true"); p.set_defaults(func=cmd_keygen)
    p = sub.add_parser("pack"); p.add_argument("input"); p.add_argument("--store", default=".arc_apache"); p.add_argument("--content-class", default="generic_blob"); p.add_argument("--codec", default="raw"); p.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE); p.add_argument("--parent", action="append"); p.add_argument("--encrypt", action="store_true"); p.add_argument("--key-out"); p.set_defaults(func=cmd_pack)
    p = sub.add_parser("verify"); p.add_argument("manifest"); p.add_argument("--store", default=".arc_apache"); p.set_defaults(func=cmd_verify)
    p = sub.add_parser("restore"); p.add_argument("manifest"); p.add_argument("output"); p.add_argument("--store", default=".arc_apache"); p.add_argument("--envelope", action="store_true"); p.add_argument("--key"); p.set_defaults(func=cmd_restore)
    p = sub.add_parser("receipt"); p.add_argument("manifest"); p.add_argument("--store", default=".arc_apache"); p.add_argument("--source", required=True); p.add_argument("--receipt-type", default="payload.registered"); p.add_argument("--policy-status", default="accepted"); p.add_argument("--actor", default="local-operator"); p.add_argument("--parent", action="append"); p.set_defaults(func=cmd_receipt)
    p = sub.add_parser("sign-receipt"); p.add_argument("receipt"); p.add_argument("--store", default=".arc_apache"); p.add_argument("--key-name", required=True); p.set_defaults(func=cmd_sign_receipt)
    p = sub.add_parser("verify-receipt"); p.add_argument("receipt"); p.add_argument("--store", default=".arc_apache"); p.set_defaults(func=cmd_verify_receipt)
    p = sub.add_parser("mirror-language"); p.add_argument("language_root"); p.add_argument("--store", default=".arc_apache"); p.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE); p.add_argument("--out", default="language_binary_mirror_report.json"); p.set_defaults(func=cmd_mirror_language)
    p = sub.add_parser("stream-manifest"); p.add_argument("frames_dir"); p.add_argument("--stream-id", required=True); p.add_argument("--source", default="streammemory"); p.add_argument("--codec", default="raw-frame"); p.add_argument("--store", default=".arc_apache"); p.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE); p.add_argument("--out"); p.set_defaults(func=cmd_stream_manifest)
    p = sub.add_parser("sure-recipe"); p.add_argument("--generator", required=True); p.add_argument("--generator-version", default="unknown"); p.add_argument("--seed", required=True); p.add_argument("--params"); p.add_argument("--environment", default="unspecified"); p.add_argument("--expected-output-sha256"); p.add_argument("--notes", default=""); p.add_argument("--store", default=".arc_apache"); p.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE); p.set_defaults(func=cmd_sure_recipe)
    p = sub.add_parser("bundle-plan"); p.add_argument("--name", required=True); p.add_argument("--manifest", action="append", required=True); p.add_argument("--receipt", action="append"); p.add_argument("--out", required=True); p.set_defaults(func=cmd_bundle_plan)
    p = sub.add_parser("smoke"); p.add_argument("--store", default=".arc_apache_smoke"); p.set_defaults(func=cmd_smoke)
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
