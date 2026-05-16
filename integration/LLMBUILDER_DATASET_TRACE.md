# LLMBuilder Dataset Trace Contract

Each dataset row should keep source proof:

```json
{
  "input": "human-readable projection",
  "target": "human-readable projection",
  "source_payload_sha256": "...",
  "source_manifest_sha256": "...",
  "source_receipt_sha256": "...",
  "language_snapshot_manifest": "...",
  "view_generation_tool": "arc-apache-viewer-vX"
}
```

Rules:

1. Do not train from unreceipted mystery text.
2. Keep dataset transforms as their own binary objects.
3. Promote models only when benchmark receipts point back to dataset receipts.
