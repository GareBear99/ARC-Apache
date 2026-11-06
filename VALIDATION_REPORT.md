# ARC-Apache v5 Validation Report

Validation run completed locally in the package directory.
Re-run after the v0.5.1 repository professionalization (the v5 manifest
format itself is unchanged).

## Commands executed

```bash
python3 scripts/arc_apache.py smoke --store .arc_apache_smoke
python3 -m pytest -q tests
```

## Result

```text
ARC-Apache v5 smoke test passed
11 passed
```

Additional manual cryptographic path checked:

- initialized store
- generated Ed25519 keypair
- packed sample object
- created receipt
- signed receipt
- verified signed receipt

Result: signed receipt verification returned `ok: true`.

## v5 format check (v0.5.1)

- A fixed payload re-packed after the changes produces the identical
  deterministic v5 fields (envelope SHA-256, Merkle root, chunk hashes,
  object ID, envelope size) as before the changes.
- A manifest produced before the changes still verifies and restores
  byte-identically with the current code.
- Tampered or missing chunks fail `verify`/`restore` as expected
  (covered by `tests/test_v5_proof.py`).
