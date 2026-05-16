# Changelog

## v4.0.0

- Promoted binary-first doctrine to package-level rule.
- Added production-facing README and public positioning guide.
- Added dependency-free `arc_apache.py` CLI with `pack`, `verify`, `restore`, `receipt`, `mirror-language`, and `sure-recipe` commands.
- Added smoke test script.
- Added schemas for binary manifests, receipts, language links, and SURE recipes.
- Added ARC-Core, Language Module, and LLMBuilder integration stubs.
- Added explicit cryptography boundary: hash/Merkle/receipt now; signatures/encryption are future audited extensions, not faked.
