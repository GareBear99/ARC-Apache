# ARC-Apache Contracts v5

## Payload registration event

```json
{
  "event_type": "payload.registered",
  "manifest_sha256": "...",
  "envelope_sha256": "...",
  "merkle_root": "...",
  "receipt_sha256": "...",
  "source": "arc-language-module | arc-streammemory | llmbuilder | runtime | manual",
  "policy_status": "accepted | quarantine | rejected | promoted"
}
```

## Receipt policy states

- `accepted`: verified and usable.
- `quarantine`: stored but not trusted for promotion.
- `rejected`: retained for audit, not used.
- `promoted`: accepted and part of a model/runtime promotion chain.

## Parent/derived object rule

Never overwrite proof history. If an object is transformed, redacted, compressed, trained on, summarized, or converted, create a new object with parent manifest hashes.
