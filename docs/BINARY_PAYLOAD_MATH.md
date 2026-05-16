# Binary Payload Mathematics

Let payload bytes be `P`.

ARC-Apache wraps `P` into an envelope `E`:

```text
E = MAGIC || len(metadata) || len(P) || canonical_metadata || P || SHA256(P)
```

The envelope hash is:

```text
H_E = SHA256(E)
```

The envelope is chunked into `n` chunks:

```text
E = C_0 || C_1 || ... || C_{n-1}
```

Each chunk hash is:

```text
h_i = SHA256(C_i)
```

The Merkle root is built pairwise:

```text
M_0 = [h_0, h_1, ..., h_{n-1}]
M_{k+1}[j] = SHA256(M_k[2j] || M_k[2j+1])
```

If a level has an odd count, duplicate the final hash. The final single hash is the Merkle root.

The manifest hash is:

```text
H_manifest = SHA256(canonical_json(manifest_without_manifest_hash + manifest_hash=null))
```

The receipt hash is:

```text
H_receipt = SHA256(canonical_json(receipt_without_receipt_hash + receipt_hash=null))
```

For SURE seeded reconstruction, ARC-Apache stores:

```text
(generator_id, generator_version, seed, parameters_hash, environment_fingerprint, expected_output_hash)
```

This lets ARC store exact bytes when exact preservation is needed, and store deterministic reconstruction recipes when the object is generated and reproducible.
