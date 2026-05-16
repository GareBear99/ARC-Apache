# Integration Blueprint v4

## Phase 1 — Standalone ARC-Apache repo

Create a new repo or module with this package. Validate the CLI first.

```bash
python tests/test_arc_apache_cli.py
```

Success means pack, verify, restore, and receipt all work without external dependencies.

## Phase 2 — ARC-Core route integration

Add ARC-Core endpoints:

```text
POST /binary/register-manifest
POST /binary/register-receipt
GET  /binary/objects/{payload_hash}
GET  /binary/manifests/{manifest_hash}
GET  /binary/receipts/{receipt_hash}
```

Payloads to ARC-Core should be small metadata objects, never raw giant binary blobs.

## Phase 3 — Language Module binary hook

On build/release/import:

```text
arc-language-module file/db -> arc-apache pack -> manifest -> receipt -> ARC-Core register
```

Add a language snapshot receipt to runtime events that use language graph semantics.

## Phase 4 — Cleanroom runtime hook

Every durable runtime boundary emits:

```text
runtime_event -> binary envelope -> manifest -> receipt
```

Examples:

- operator directive;
- model response;
- tool result;
- patch proposal;
- validation result;
- rollback point;
- memory-tier update;
- perception adapter output.

## Phase 5 — StreamMemory hook

Each frame is a binary object. Each session is a sequence manifest.

```text
frame bytes -> stream_frame object
session order -> stream_sequence manifest
summary -> disposable view linked to receipt
```

## Phase 6 — LLMBuilder hook

Every dataset row should contain source proof:

```json
{
  "text_view": "...",
  "source_payload_hash": "...",
  "source_manifest_hash": "...",
  "source_receipt_hash": "...",
  "language_snapshot_hash": "..."
}
```

Model artifacts should be packed as `model_artifact` objects and promoted only through receipt-backed benchmark gates.

## Phase 7 — Arc-RAR bundle layer

Bundle manifests, receipts, selected chunks, views, and restore instructions into a portable ARC archive.

## Phase 8 — Proto-Synth visualization

Proto-Synth renders:

- object nodes;
- receipt chains;
- Merkle trees;
- stream sequences;
- language snapshot links;
- model candidate lineage;
- SURE seed-recipe expansion graphs.

Proto-Synth is a view, not the authority.
