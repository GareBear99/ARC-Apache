# ARC Language Module Binary Hook

The language module must be connected directly to ARC-Apache.

## Required behavior

When the language module changes:

1. Pack changed seed/config/db files into binary objects.
2. Create receipts with source `arc-language-module`.
3. Register receipts with ARC-Core.
4. Use the resulting manifest hashes as the language version identity.

## Command

```bash
python scripts/arc_apache.py mirror-language ../arc-language-module-main \
  --store .arc_apache \
  --out language_binary_mirror_report.json
```

## LLMBuilder rule

LLMBuilder should not ingest language files by path alone. It should ingest:

```json
{
  "language_manifest_sha256": "...",
  "receipt_sha256": "...",
  "source": "arc-language-module",
  "policy_status": "accepted"
}
```
