# ARC-Apache SURE Binary Memory Pack v5

**ARC-Apache** is the binary-first cryptographic memory substrate for the ARC ecosystem. It treats every durable knowledge object as a deterministic binary object first, then binds that object to hashes, Merkle roots, manifests, receipts, signatures, and optional encryption.

This package is designed as the bridge between:

- **ARC-Core** — authority, receipts, policy, event registration
- **ARC Language Module** — lexical / meaning spine mirrored into binary objects
- **ARC-StreamMemory** — screen, sensor, frame, terminal, and visual memory streams
- **ARC-Neuron LLMBuilder** — datasets, candidates, GGUF/model artifacts, benchmark lineage
- **OmniBinary Runtime** — binary intake and deterministic mirror discipline
- **Arc-RAR** — portable rollback / proof bundles
- **SURE** — seeded reconstruction math for large generated payloads
- **Proto-Synth Grid Engine** — visual cognition shell for graphs, receipts, streams, and memory maps
- **ARC Lucifer Cleanroom Runtime / Cognition Core** — event-sourced runtime and promotion lanes

## Current capability

v5 provides a runnable reference implementation for the core proof loop:

```bash
python scripts/arc_apache.py init-store --store .arc_apache
python scripts/arc_apache.py keygen --store .arc_apache --name local-node
python scripts/arc_apache.py pack README.md --store .arc_apache --content-class document --codec utf8-text
python scripts/arc_apache.py verify .arc_apache/manifests/<manifest>.json --store .arc_apache
python scripts/arc_apache.py receipt .arc_apache/manifests/<manifest>.json --store .arc_apache --source manual
python scripts/arc_apache.py sign-receipt .arc_apache/receipts/<receipt>.json --store .arc_apache --key-name local-node
python scripts/arc_apache.py verify-receipt .arc_apache/receipts/<receipt>.json --store .arc_apache
```

It supports:

- deterministic binary envelopes
- chunked object storage
- SHA-256 payload hashes
- per-chunk SHA-256 hashes
- Merkle roots
- manifest hashes
- receipt hashes
- Ed25519 receipt signing when `cryptography` is installed
- AES-GCM encrypted object packing when `cryptography` is installed
- language-module binary mirroring
- stream/frame manifest generation
- SURE seed-recipe objects
- Arc-RAR bundle planning
- ARC-Core route stubs
- tests and smoke validation

## Format stability

The v5 manifest format (`schemas/binary_manifest.schema.json`, `VERSION = 5`
in `arc_apache/cli.py`) is frozen. Consumers — including ARC-Emulator, which
adopts v5 as-is — depend on the manifest fields, the envelope layout, the
chunk hashes, and the Merkle construction. A format change requires a new
version, never a silent edit to v5. `tests/test_v5_proof.py` pins the
deterministic v5 hashes for a fixed payload so a format change fails loudly.

## Repository layout

- `arc_apache/` — the v5 CLI (dependency-free core; `cryptography` optional)
- `scripts/arc_apache.py` — the CLI entry point; `scripts/regen_manifest.py` regenerates `MANIFEST.sha256.json`
- `schemas/` — JSON schemas for the v5 manifest, receipts, streams, and SURE recipes
- `tests/` — pytest suite (run with `python -m pytest`)
- `integration/` — integration contracts and stubs for ARC-Core, the Language Module, StreamMemory, LLMBuilder, and Arc-RAR
- `docs/`, `contracts/`, `math/` — specs and design docs (v4 files are marked historical)
- `examples/` — example SURE parameters

## Doctrine

```text
All durable ARC information -> canonical binary object -> cryptographic proof -> receipt -> authorized projections.
```

Text, JSON, SQLite, UI views, markdown, screenshots, source files, model files, frames, benchmark rows, and language graphs are **not the final truth surface**. They are source forms or projections. The canonical durable form is the binary object plus its proof chain.

## Install / run

No install is required for the core pack/verify/restore path. Python 3.10+ is recommended.

Optional cryptographic signing/encryption requires:

```bash
python -m pip install cryptography
```

Run tests:

```bash
python -m pytest tests
```

Run a no-pytest smoke check:

```bash
python scripts/arc_apache.py smoke --store .arc_apache_smoke
```

## Public positioning

ARC-Apache is not marketed as a finished AGI. It is a real-world substrate for systems that need memory integrity, replayability, provenance, dataset lineage, model artifact lineage, and cryptographic proof for large binary/runtime objects.

The honest claim:

> ARC-Apache gives ARC systems a binary-first, cryptographically verifiable memory layer that can support language, runtime, stream, model, and seeded-generation objects without treating loose text or opaque blobs as trusted truth.
