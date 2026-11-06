# Changelog

## v0.5.1

Repository professionalization. The v5 manifest format is unchanged
(`schemas/binary_manifest.schema.json`, `VERSION = 5` in the CLI).

- Adds `.gitignore` (Python caches, venvs, ARC-Apache stores, key files).
- Adds CI (`.github/workflows/smoke.yml`): pytest + smoke on Python 3.10/3.11/3.12.
- Removes the stale `src/arc_apache/` v4 tree (superseded by the root `arc_apache/` v5 package).
- Marks the v4 docs as historical (superseded by v5).
- Fixes the ARC-Core route stub example payload to version 5 and documents
  that the route itself lives in ARC-Core (not wired from this side).
- Adds proof-plane tests: tampered/missing chunks must fail verify/restore,
  a v5 format pin (deterministic manifest hashes for a fixed payload),
  receipt sign/verify round-trip, and ARC-Core route model validation.
- Adds a `[build-system]` declaration and a `scripts/regen_manifest.py`
  helper; `MANIFEST.sha256.json` is regenerated to cover the current tree.
- Test suite grows from 3 to 11 tests, 0 failures.

## v0.5.0

- Adds repository-ready ARC-Apache package structure.
- Adds deterministic binary envelope format v5.
- Adds chunked object store, manifest, receipt, restore, and verify commands.
- Adds optional Ed25519 receipt signing and verification.
- Adds optional AES-GCM encrypted packing mode.
- Adds stream sequence manifest generation for ARC-StreamMemory.
- Adds language mirror command for ARC Language Module.
- Adds SURE seed recipe object support.
- Adds ARC-Core route and storage integration stubs.
- Adds LLMBuilder, Cognition Core, Runtime, Arc-RAR, OmniBinary, Turbo, and Proto-Synth integration docs.
- Adds tests and smoke command.
