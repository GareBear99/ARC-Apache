# ARC-Apache: binary-first memory for ARC systems

I built ARC-Apache as the binary-first cryptographic memory substrate for my ARC ecosystem.

The idea is simple: durable AI/runtime knowledge should not live as loose text, random JSON, or unverified blobs. Every important object should become a deterministic binary payload first, then get chunked, hashed, Merkle-rooted, receipted, and optionally signed/encrypted.

Current v5 package includes:

- binary envelope format
- chunk store
- Merkle manifests
- receipt generation
- optional Ed25519 signing
- optional AES-GCM encrypted packing
- StreamMemory frame sequence support
- ARC Language Module binary mirroring
- LLMBuilder lineage contracts
- ARC-Core route stubs
- SURE seeded reconstruction recipe support

This is not being marketed as a finished AGI. It is the proof/memory/replay substrate that a serious local-first AI architecture needs underneath it.
