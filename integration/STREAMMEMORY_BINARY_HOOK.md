# ARC-StreamMemory Binary Hook

ARC-StreamMemory should emit a stream sequence manifest instead of relying on loose frame folders.

```bash
python scripts/arc_apache.py stream-manifest ./frames \
  --stream-id desktop_capture_2026_05_16 \
  --source arc-streammemory \
  --codec png-frame \
  --store .arc_apache
```

Each frame is independently hash-addressed and restorable. The sequence manifest links frames into time order.

Privacy rule: redaction should produce a new derived frame manifest with the original frame as a parent, not overwrite the original proof chain.
