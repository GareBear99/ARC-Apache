# ARC-Neuron LLMBuilder Binary Lineage Contract

Promotable model artifacts must trace back to receipted binary manifests.

## Dataset group

```json
{
  "dataset_group_id": "arc-language-wave-001",
  "manifest_sha256": "...",
  "receipt_sha256": "...",
  "policy_status": "accepted"
}
```

## Candidate model

```json
{
  "candidate_id": "candidate-v3-wave-001",
  "model_manifest_sha256": "...",
  "tokenizer_manifest_sha256": "...",
  "training_data_manifest_sha256": "...",
  "benchmark_receipt_sha256": "..."
}
```

## Promotion gate

No candidate should be promoted if its dataset, tokenizer, model artifact, benchmark output, and evaluator receipts are not all traceable.
