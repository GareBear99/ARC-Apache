# ARC-Apache Contracts v4

## Contract 1 — Binary-first truth

Every durable fact must have a binary object identity before it becomes canonical ARC memory.

## Contract 2 — Views are disposable

Text, JSON, summaries, embeddings, dashboards, SQLite indexes, and UI graphs are regenerated projections.

## Contract 3 — ARC-Core is authority, not blob storage

ARC-Core registers receipts, policy, actors, and lineage. It does not hold giant payload bytes.

## Contract 4 — Language Module is the lexical spine

ARC Language Module snapshots are mirrored as binary objects and linked to runtime/model/dataset events that depend on language semantics.

## Contract 5 — Cryptographic minimum

Every object requires:

- payload SHA-256;
- chunk SHA-256 hashes;
- Merkle root;
- manifest SHA-256;
- receipt SHA-256 for registered events.

## Contract 6 — Signatures and encryption must not be faked

Until key management is implemented, v4 is hash/Merkle/receipt proof. Future signing should use Ed25519 or equivalent. Future encryption should use audited AEAD such as AES-256-GCM, XChaCha20-Poly1305, age, or libsodium.

## Contract 7 — No silent overwrite

All mutation produces a new object and receipt. Old objects remain addressable.

## Contract 8 — Model training traceability

LLMBuilder training/evaluation rows must be traceable to source binary payloads and receipts.

## Contract 9 — SURE recipe honesty

A seed recipe is not equivalent to preserved bytes unless the generator, version, parameters, environment, and expected output hash are sufficient to reproduce or falsify the output.

## Contract 10 — Public professionalism

Public docs must distinguish current executable features from roadmap items. Claims must be evidence-backed and testable.
