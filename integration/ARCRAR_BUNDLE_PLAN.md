# Arc-RAR Bundle Plan

Arc-RAR should bundle:

- manifests
- receipts
- optional chunks
- lineage map
- policy summary
- restore script
- release hash file

Use:

```bash
python scripts/arc_apache.py bundle-plan \
  --name language-wave-001 \
  --manifest .arc_apache/manifests/<manifest>.json \
  --receipt .arc_apache/receipts/<receipt>.json \
  --out bundle_plan.json
```

This creates a proof plan that Arc-RAR can turn into a portable archive.
