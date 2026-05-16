# Security Policy

ARC-Apache v5 is a reference implementation for binary-first proof chains. It includes real SHA-256, Merkle roots, receipt hashes, optional Ed25519 signing, and optional AES-GCM encryption when the `cryptography` package is available.

## Security boundaries

- Hashes prove object integrity, not author intent.
- Merkle roots prove chunk-set integrity, not semantic correctness.
- Receipts bind ARC metadata to payload proofs, but must still be accepted by ARC-Core policy.
- Signatures prove the holder of a private key signed a receipt.
- Encryption protects object bytes at rest only if keys are managed correctly.

## Do not claim

- Do not claim this is a finished AGI.
- Do not claim encrypted storage is secure without key management review.
- Do not claim signed receipts are trusted unless ARC-Core has a trust policy for the signer.

## Recommended production hardening

- Move private keys out of `.arc_apache/keys/private` before production.
- Use OS keychain, HSM, age, SOPS, or a custody-managed vault for private material.
- Add signed release manifests.
- Add reproducible build checks.
- Add ARC-Core policy review before accepting receipts.
