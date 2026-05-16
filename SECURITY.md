# Security Policy

ARC-Apache v4 provides hash/Merkle/receipt integrity checks. It does not yet provide audited encryption or public-key signing in the reference CLI.

## Current guarantees

- SHA-256 payload identity;
- SHA-256 chunk identity;
- deterministic Merkle root;
- manifest hash;
- receipt hash;
- deterministic restore verification.

## Not yet guaranteed by the reference CLI

- confidentiality;
- identity/authorship signatures;
- tamper-proof remote storage;
- hardware-backed key custody.

Future cryptographic extensions should use audited libraries and formats such as Ed25519, XChaCha20-Poly1305, AES-256-GCM, age, minisign, Sigstore, or hardware-backed keys.
