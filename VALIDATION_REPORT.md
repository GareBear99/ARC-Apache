# ARC-Apache v5 Validation Report

Validation run completed locally in the package directory.

## Commands executed

```bash
python3 scripts/arc_apache.py smoke --store .arc_apache_smoke
python3 -m pytest -q tests
```

## Result

```text
ARC-Apache v5 smoke test passed
3 passed
```

Additional manual cryptographic path checked:

- initialized store
- generated Ed25519 keypair
- packed sample object
- created receipt
- signed receipt
- verified signed receipt

Result: signed receipt verification returned `ok: true`.
