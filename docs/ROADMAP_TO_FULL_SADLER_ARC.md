# Roadmap to the Full Sadler-Style ARC System

Alec Sadler's ARC is a fictional finished intelligence system. ARC-Apache v5 is the real-world substrate that makes such a system technically safer: proof first, memory second, cognition third.

## Phase 1 — Binary proof spine complete

Status: implemented in v5 reference package.

- Binary envelopes
- Chunk store
- Merkle roots
- Manifests
- Receipts
- Optional signatures
- Optional encryption
- Restore/verify path

## Phase 2 — ARC-Core authority integration

Next implementation target.

- Register manifests in ARC-Core.
- Register receipts in ARC-Core.
- Add policy status: accepted, quarantine, rejected, promoted.
- Add trusted key registry.
- Add SQLite table migrations for payloads and receipts.

## Phase 3 — Language spine lock

- Mirror `arc-language-module` to binary objects.
- Register language receipts in ARC-Core.
- Add language version receipts.
- LLMBuilder consumes language manifests by hash, not loose files.

## Phase 4 — StreamMemory live ingestion

- Capture frames/screens/terminal states.
- Pack each frame as binary.
- Build stream sequence manifests.
- Register stream receipts.
- Add privacy gates and redaction receipts.

## Phase 5 — LLMBuilder lineage integration

- Dataset row groups become binary manifests.
- Tokenizer artifacts become binary manifests.
- GGUF/model candidates become binary manifests.
- Benchmark outputs become binary manifests.
- Promotion requires receipt chain.

## Phase 6 — Proto-Synth visual shell

- Visualize manifests as nodes.
- Visualize receipt chains.
- Visualize stream sequences.
- Visualize model lineage and rollback points.

## Phase 7 — Distributed storage / replication

- Add replication policy.
- Add chunk availability maps.
- Add self-healing chunk copy checks.
- Add cold/hot tier movement.

## Honest comparison

ARC-Apache is not yet an autonomous future-predicting ARC. It is the memory, proof, replay, and authority substrate that a real system would need before higher cognition can be safely promoted.
