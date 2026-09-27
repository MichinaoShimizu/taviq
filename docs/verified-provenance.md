# Verified Provenance Threat Model

## Goal

Taviq distinguishes three claims:
1. Recorded — provenance metadata exists.
2. Taviq-verified — metadata was produced/signed by a configured Taviq installation and has not been modified.
3. Vendor-attested — the AI vendor/runtime itself cryptographically attests the execution.

v0.1 targets level 2. Level 2 is not proof from Claude, Codex, Kiro, or another vendor.

## Threats

### Manual trailer spoofing
A developer can type Taviq metadata manually. Unsigned trailers remain recorded/unverified.

### Trailer modification
A signed provenance payload that is edited must fail verification.

### Key theft
Anyone with an HMAC key can create Taviq-verified records. Keys must be scoped, protected and rotatable.

### Compromised local machine
A compromised workstation can invoke a local signer with false metadata. v0.1 does not solve this. Taviq-verified means accepted by the configured Taviq signer, not vendor-independent proof.

### Replay
Signatures must include repository scope and a unique provenance reference. Strong immutable commit-bound attestations remain future work because signing data embedded in the commit message has a commit-hash circularity problem.

## UI language

Allowed: Verified by Taviq; Recorded, unverified; Unknown; Vendor-attested only when such an attestation exists.

Do not say Verified by Claude when only Taviq signed it. Do not say AI definitely wrote this code. Unknown is not human-only.

## v0.1 cryptography

HMAC-SHA256 is acceptable only as an MVP integrity mechanism. It is symmetric, so a verifier holding the secret can also sign.

Production direction: asymmetric signatures or established software supply-chain attestation formats, with signing capability separated from CI verification.