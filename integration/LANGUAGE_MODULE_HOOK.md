# ARC Language Module Hook

## Goal

Make the ARC Language Module a first-class binary memory source.

## Build/release command

```bash
python ../ARC-Apache/scripts/arc_apache.py mirror-language . --store ../ARC-Apache/.arc_apache --out language_binary_mirror_report.json
```

## Runtime link

Runtime events that depend on language semantics should include:

```json
{
  "language_snapshot_manifest": "<manifest_hash>",
  "language_db_payload_hash": "<payload_hash>",
  "promotion_policy": "semantic-link-only-until-validated"
}
```

The binary mirror proves which language data existed. It does not automatically promote new semantics into model weights.
