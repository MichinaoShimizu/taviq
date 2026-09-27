# Provenance Trust Model

## Principle
Taviq Basic does not introduce a custom signing secret, key-management system, or proprietary verification protocol.

Basic records explicit provenance metadata and reports two core states:
- Recorded — Taviq provenance metadata is present.
- Unknown — provenance evidence is absent.

Recorded does not mean cryptographically verified and does not mean the AI vendor independently attested the execution.

## Why
Adding a custom shared secret would create new operational and security risks: secret distribution, CI secret exposure, rotation, compromise handling, verifier/signing ambiguity, and false confidence from a Verified label.

Taviq Basic prioritizes zero server, zero secret, low privilege, and transparent evidence semantics.

## Spoofing
A commit trailer can be manually created or edited. Basic therefore treats trailers as recorded metadata, not tamper-proof evidence.

Do not display Verified by Taviq, Verified by Claude, Verified by Codex, or Verified by Kiro from Basic trailers.

## Future stronger provenance
If customers require cryptographic verification, Taviq should first evaluate established signing and software supply-chain attestation mechanisms instead of inventing its own key system.

Candidate directions include signed Git identities/objects, Sigstore-style signing, SLSA/in-toto style provenance, and GitHub-supported artifact attestations where they fit the actual execution model.

Any future mechanism must preserve the distinction between:
- Taviq recorded metadata
- cryptographically verifiable producer identity
- vendor-attested AI execution

Unknown must never be converted to human-only by inference.