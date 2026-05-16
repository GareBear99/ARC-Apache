# ARC-Apache v5 Architecture

## Non-negotiable rule

ARC stores durable information as binary first.

```text
source form -> ARC binary envelope -> chunk store -> manifest -> receipt -> ARC-Core policy registration -> authorized projections
```

## Layer map

| Layer | Responsibility | Canonical storage behavior |
|---|---|---|
| ARC-Core | Authority, receipts, policy, registration | Stores hashes/receipts, not large blobs |
| ARC-Apache | Binary envelope, chunking, Merkle, signing, encryption | Stores canonical binary objects |
| ARC Language Module | Lexical / meaning spine | Mirrored into binary manifests |
| ARC-StreamMemory | Screens, frames, sensors, terminal streams | Sequence manifests + per-frame binary objects |
| LLMBuilder | Dataset/model/benchmark lineage | Consumes verified manifests and receipts |
| Cognition Core | Candidate scoring and promotion | Requires traceable receipts for promotable artifacts |
| Lucifer Runtime | Event-sourced runtime | Emits binary event snapshots and replay anchors |
| OmniBinary | Binary intake discipline | Mirrors and classifies binary surfaces |
| SURE | Seeded reconstruction math | Stores seed recipes and expected output hashes |
| Arc-RAR | Portable rollback/proof bundles | Bundles manifests, receipts, chunks, lineage |
| Proto-Synth | Visual cognition shell | Visualizes graph, receipt chains, streams |

## Object model

An ARC-Apache object is not just a file. It is:

1. Original source bytes or canonicalized object bytes.
2. ARC-Apache binary envelope.
3. Chunk list.
4. Chunk hashes.
5. Merkle root.
6. Manifest hash.
7. Receipt hash.
8. Optional receipt signature.
9. Optional encryption metadata.

## Trust model

- Binary envelope proves what bytes were stored.
- Chunk hashes prove shard integrity.
- Merkle root proves chunk-set consistency.
- Manifest hash proves the object description did not change.
- Receipt hash proves ARC metadata did not change.
- Signature proves a key signed the receipt.
- ARC-Core policy determines whether the receipt is accepted into the authority layer.
