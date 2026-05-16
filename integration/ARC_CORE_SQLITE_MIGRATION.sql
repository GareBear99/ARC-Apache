-- ARC-Apache v5 payload/receipt registry tables for ARC-Core.

CREATE TABLE IF NOT EXISTS arc_payload_manifests (
  manifest_sha256 TEXT PRIMARY KEY,
  envelope_sha256 TEXT NOT NULL,
  merkle_root TEXT NOT NULL,
  content_class TEXT NOT NULL,
  source TEXT NOT NULL,
  policy_status TEXT NOT NULL DEFAULT 'quarantine',
  created_utc TEXT NOT NULL,
  registered_utc TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS arc_payload_receipts (
  receipt_sha256 TEXT PRIMARY KEY,
  manifest_sha256 TEXT NOT NULL,
  receipt_type TEXT NOT NULL,
  source TEXT NOT NULL,
  actor TEXT,
  signed INTEGER NOT NULL DEFAULT 0,
  signature_key_name TEXT,
  policy_status TEXT NOT NULL DEFAULT 'quarantine',
  created_utc TEXT NOT NULL,
  registered_utc TEXT NOT NULL,
  FOREIGN KEY(manifest_sha256) REFERENCES arc_payload_manifests(manifest_sha256)
);

CREATE INDEX IF NOT EXISTS idx_arc_payload_manifests_source ON arc_payload_manifests(source);
CREATE INDEX IF NOT EXISTS idx_arc_payload_receipts_manifest ON arc_payload_receipts(manifest_sha256);
