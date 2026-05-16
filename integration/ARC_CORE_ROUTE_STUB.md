# ARC-Core Route Stub

Add these routes in ARC-Core after reviewing current app structure:

```text
POST /binary/register-manifest
POST /binary/register-receipt
GET  /binary/manifests/{manifest_hash}
GET  /binary/receipts/{receipt_hash}
```

Minimal register-manifest payload:

```json
{
  "version": 4,
  "payload_sha256": "...",
  "manifest_sha256": "...",
  "merkle_root": "...",
  "content_class": "runtime_event",
  "source": "arc-lucifer-cleanroom-runtime",
  "policy_status": "accepted"
}
```

Do not send raw blob bytes to ARC-Core. Send metadata and store chunks in ARC-Apache object storage.
