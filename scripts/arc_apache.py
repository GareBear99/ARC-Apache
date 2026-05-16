#!/usr/bin/env python3
"""ARC-Apache binary memory CLI v4.

Dependency-free reference implementation:
- pack: binary envelope + chunk store + manifest
- verify: verify chunks, payload hash, Merkle root, manifest hash
- restore: rebuild envelope bytes from chunk store
- receipt: create a hash-bound ARC receipt for a manifest
- mirror-language: pack known ARC Language Module files
- sure-recipe: create and pack a SURE seed recipe object

This implementation intentionally does not fake encryption or digital signatures.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import struct
import sys
from pathlib import Path
from typing import Any, Iterable

MAGIC = b"ARC_BIN\0"
VERSION = 4
DEFAULT_CHUNK = 1024 * 1024
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
    return _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json_bytes(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def merkle_root(hex_hashes: list[str]) -> str:
    if not hex_hashes:
        return sha256_bytes(b"")
    level = [bytes.fromhex(h) for h in hex_hashes]
    while len(level) > 1:
        if len(level) % 2 == 1:
            level.append(level[-1])
        level = [hashlib.sha256(level[i] + level[i + 1]).digest() for i in range(0, len(level), 2)]
    return level[0].hex()


def make_envelope(payload: bytes, content_class: str, codec: str) -> bytes:
    cc = content_class.encode("utf-8")
    co = codec.encode("utf-8")
    header = MAGIC + struct.pack(">HIIQ", VERSION, len(cc), len(co), len(payload)) + cc + co
    footer = hashlib.sha256(payload).digest()
    return header + payload + footer


def parse_envelope(envelope: bytes) -> dict[str, Any]:
    if not envelope.startswith(MAGIC):
        raise ValueError("not an ARC binary envelope")
    off = len(MAGIC)
    version, cc_len, co_len, payload_len = struct.unpack(">HIIQ", envelope[off:off+18])
    off += 18
    content_class = envelope[off:off+cc_len].decode("utf-8")
    off += cc_len
    codec = envelope[off:off+co_len].decode("utf-8")
    off += co_len
    payload = envelope[off:off+payload_len]
    off += payload_len
    footer = envelope[off:off+32]
    if hashlib.sha256(payload).digest() != footer:
        raise ValueError("ARC envelope footer hash mismatch")
    return {"version": version, "content_class": content_class, "codec": codec, "payload": payload}


def store_chunk(store: Path, chunk: bytes) -> tuple[str, str]:
    h = sha256_bytes(chunk)
    rel = Path("objects") / "sha256" / h[:2] / h[2:4] / f"{h}.bin"
    p = store / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists():
        p.write_bytes(chunk)
    return h, str(rel)


def read_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def pack_bytes(data: bytes, *, store: Path, content_class: str, codec: str, source_path: str | None, chunk_size: int, parents: list[str] | None = None, sure_recipe: dict[str, Any] | None = None, language_link: dict[str, Any] | None = None) -> dict[str, Any]:
    store.mkdir(parents=True, exist_ok=True)
    envelope = make_envelope(data, content_class, codec)
    payload_hash = sha256_bytes(envelope)
    chunks = []
    chunk_hashes = []
    for idx in range(0, len(envelope), chunk_size):
        chunk = envelope[idx:idx + chunk_size]
        h, rel = store_chunk(store, chunk)
        chunk_hashes.append(h)
        chunks.append({"index": len(chunks), "sha256": h, "size_bytes": len(chunk), "store_path": rel})
    manifest = {
        "version": VERSION,
        "object_id": f"arcbin:{payload_hash}",
        "content_class": content_class,
        "codec": codec,
        "payload_sha256": payload_hash,
        "size_bytes": len(envelope),
        "chunk_size": chunk_size,
        "chunks": chunks,
        "merkle_root": merkle_root(chunk_hashes),
        "source_path": source_path,
        "parents": parents or [],
        "created_utc": utc_now(),
    }
    if sure_recipe is not None:
        manifest["sure_recipe"] = sure_recipe
    if language_link is not None:
        manifest["language_link"] = language_link
    unsigned = dict(manifest)
    unsigned["manifest_sha256"] = None
    mh = sha256_bytes(canonical_json_bytes(unsigned))
    manifest["manifest_sha256"] = mh
    out = store / "manifests" / f"{mh}.json"
    write_json(out, manifest)
    return manifest


def cmd_pack(args: argparse.Namespace) -> int:
    p = Path(args.input)
    data = p.read_bytes()
    manifest = pack_bytes(data, store=Path(args.store), content_class=args.content_class, codec=args.codec, source_path=str(p), chunk_size=args.chunk_size, parents=args.parent or [])
    print(json.dumps({"manifest_sha256": manifest["manifest_sha256"], "payload_sha256": manifest["payload_sha256"], "merkle_root": manifest["merkle_root"], "chunks": len(manifest["chunks"]), "manifest_path": str(Path(args.store)/"manifests"/f"{manifest['manifest_sha256']}.json")}, indent=2))
    return 0


def verify_manifest(manifest: dict[str, Any], store: Path) -> tuple[bool, list[str]]:
    errors: list[str] = []
    rebuilt = bytearray()
    chunk_hashes = []
    for ch in sorted(manifest["chunks"], key=lambda x: x["index"]):
        p = store / ch["store_path"]
        if not p.exists():
            errors.append(f"missing chunk: {p}")
            continue
        data = p.read_bytes()
        h = sha256_bytes(data)
        if h != ch["sha256"]:
            errors.append(f"chunk hash mismatch: {p}")
        if len(data) != ch["size_bytes"]:
            errors.append(f"chunk size mismatch: {p}")
        rebuilt.extend(data)
        chunk_hashes.append(h)
    if sha256_bytes(bytes(rebuilt)) != manifest["payload_sha256"]:
        errors.append("payload_sha256 mismatch")
    if merkle_root(chunk_hashes) != manifest["merkle_root"]:
        errors.append("merkle_root mismatch")
    unsigned = dict(manifest)
    expected = unsigned.pop("manifest_sha256")
    unsigned["manifest_sha256"] = None
    actual = sha256_bytes(canonical_json_bytes(unsigned))
    if actual != expected:
        errors.append("manifest_sha256 mismatch")
    try:
        parse_envelope(bytes(rebuilt))
    except Exception as e:
        errors.append(f"envelope parse failed: {e}")
    return not errors, errors


def cmd_verify(args: argparse.Namespace) -> int:
    manifest = read_manifest(Path(args.manifest))
    ok, errors = verify_manifest(manifest, Path(args.store))
    print(json.dumps({"ok": ok, "errors": errors, "manifest_sha256": manifest.get("manifest_sha256")}, indent=2))
    return 0 if ok else 2


def cmd_restore(args: argparse.Namespace) -> int:
    manifest = read_manifest(Path(args.manifest))
    ok, errors = verify_manifest(manifest, Path(args.store))
    if not ok:
        print(json.dumps({"ok": False, "errors": errors}, indent=2), file=sys.stderr)
        return 2
    envelope = b"".join((Path(args.store) / ch["store_path"]).read_bytes() for ch in sorted(manifest["chunks"], key=lambda x: x["index"]))
    parsed = parse_envelope(envelope)
    if args.envelope:
        Path(args.output).write_bytes(envelope)
    else:
        Path(args.output).write_bytes(parsed["payload"])
    print(json.dumps({"ok": True, "output": args.output, "wrote_envelope": bool(args.envelope), "content_class": parsed["content_class"], "codec": parsed["codec"]}, indent=2))
    return 0


def cmd_receipt(args: argparse.Namespace) -> int:
    manifest = read_manifest(Path(args.manifest))
    receipt = {
        "version": VERSION,
        "receipt_type": args.receipt_type,
        "source": args.source,
        "payload_sha256": manifest["payload_sha256"],
        "manifest_sha256": manifest["manifest_sha256"],
        "merkle_root": manifest["merkle_root"],
        "policy_status": args.policy_status,
        "parent_receipts": args.parent or [],
        "actor": args.actor,
        "created_utc": utc_now(),
    }
    unsigned = dict(receipt)
    unsigned["receipt_sha256"] = None
    rh = sha256_bytes(canonical_json_bytes(unsigned))
    receipt["receipt_sha256"] = rh
    out = Path(args.store) / "receipts" / f"{rh}.json"
    write_json(out, receipt)
    print(json.dumps({"receipt_sha256": rh, "receipt_path": str(out)}, indent=2))
    return 0


def cmd_mirror_language(args: argparse.Namespace) -> int:
    root = Path(args.language_root)
    report = {"language_root": str(root), "packed": [], "missing": [], "created_utc": utc_now()}
    for rel in LANGUAGE_TARGETS:
        p = root / rel
        if not p.exists():
            report["missing"].append(rel)
            continue
        manifest = pack_bytes(p.read_bytes(), store=Path(args.store), content_class="language_graph", codec="arc-language-file", source_path=str(p), chunk_size=args.chunk_size)
        report["packed"].append({"source": rel, "manifest_sha256": manifest["manifest_sha256"], "payload_sha256": manifest["payload_sha256"]})
    out = Path(args.out)
    write_json(out, report)
    print(json.dumps({"packed": len(report["packed"]), "missing": len(report["missing"]), "report": str(out)}, indent=2))
    return 0


def cmd_sure_recipe(args: argparse.Namespace) -> int:
    params_path = Path(args.params)
    params = json.loads(params_path.read_text(encoding="utf-8")) if params_path.exists() else {}
    params_hash = sha256_bytes(canonical_json_bytes(params))
    recipe = {
        "version": VERSION,
        "generator_id": args.generator,
        "generator_version": args.generator_version,
        "seed": args.seed,
        "parameters_sha256": params_hash,
        "parameters": params,
        "environment_fingerprint": args.environment,
        "expected_output_sha256": args.expected_output_sha256,
        "notes": args.notes,
        "created_utc": utc_now(),
    }
    data = canonical_json_bytes(recipe)
    manifest = pack_bytes(data, store=Path(args.store), content_class="seed_recipe", codec="arc-json-canonical", source_path=str(params_path), chunk_size=args.chunk_size, sure_recipe={k: v for k, v in recipe.items() if k != "parameters"})
    print(json.dumps({"manifest_sha256": manifest["manifest_sha256"], "payload_sha256": manifest["payload_sha256"], "parameters_sha256": params_hash}, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="arc-apache", description="ARC-Apache binary memory CLI v4")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("pack")
    p.add_argument("input")
    p.add_argument("--store", default=".arc_apache")
    p.add_argument("--content-class", default="generic_blob")
    p.add_argument("--codec", default="raw")
    p.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK)
    p.add_argument("--parent", action="append")
    p.set_defaults(func=cmd_pack)

    p = sub.add_parser("verify")
    p.add_argument("manifest")
    p.add_argument("--store", default=".arc_apache")
    p.set_defaults(func=cmd_verify)

    p = sub.add_parser("restore")
    p.add_argument("manifest")
    p.add_argument("output")
    p.add_argument("--store", default=".arc_apache")
    p.add_argument("--envelope", action="store_true", help="write ARC envelope instead of original payload")
    p.set_defaults(func=cmd_restore)

    p = sub.add_parser("receipt")
    p.add_argument("manifest")
    p.add_argument("--store", default=".arc_apache")
    p.add_argument("--source", required=True)
    p.add_argument("--receipt-type", default="payload.registered")
    p.add_argument("--policy-status", default="accepted")
    p.add_argument("--actor", default="local-operator")
    p.add_argument("--parent", action="append")
    p.set_defaults(func=cmd_receipt)

    p = sub.add_parser("mirror-language")
    p.add_argument("language_root")
    p.add_argument("--store", default=".arc_apache")
    p.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK)
    p.add_argument("--out", default="language_binary_mirror_report.json")
    p.set_defaults(func=cmd_mirror_language)

    p = sub.add_parser("sure-recipe")
    p.add_argument("--generator", required=True)
    p.add_argument("--generator-version", default="unknown")
    p.add_argument("--seed", required=True)
    p.add_argument("--params", required=True)
    p.add_argument("--environment", default="unspecified")
    p.add_argument("--expected-output-sha256")
    p.add_argument("--notes", default="")
    p.add_argument("--store", default=".arc_apache")
    p.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK)
    p.set_defaults(func=cmd_sure_recipe)
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
