# Verified Provenance Setup (HMAC MVP)

Verified Provenance is optional. Basic provenance works without a signing key.

## What HMAC verification means
A Verified record means the provenance metadata matches a signature created with the configured Taviq key.
It does not mean Claude, Codex, Kiro, or another vendor independently attested the execution.

## Generate a repository-scoped key
Use a cryptographically random secret, for example:
python3 -c 'import secrets; print(secrets.token_hex(32))'

Do not reuse the same key across unrelated organizations. Prefer repository- or tightly scoped organization-level keys.

## Producer environment
Expose TAVIQ_SIGNING_KEY, TAVIQ_REPOSITORY, and a unique TAVIQ_PROVENANCE_REF only to the trusted signing process.

Never write the signing key to Git, commit trailers, runtime metadata, logs, provenance envelopes, or PR comments.

## GitHub Actions verification
Create a repository Actions secret named TAVIQ_SIGNING_KEY. The Basic workflow reads it only during verification and must never print it.

## Rotation
HMAC MVP currently supports one active verification key.
1. Generate a new key.
2. Update the trusted producer.
3. Update the GitHub Actions secret.
4. Treat old-key signatures as historical/unverified unless retained verification is explicitly implemented.
5. Record rotation dates outside Git history when audit requirements need them.

Multi-key verification with key IDs is future work.

## Compromise
If the key may have leaked: stop trusting new HMAC records, rotate the key, mark the affected window as potentially compromised, and never relabel these records as vendor-attested.

## Production direction
HMAC is an MVP. Verifier and signer share a secret, so a verifier can also forge signatures.
Production should move toward asymmetric signatures or established software supply-chain attestation mechanisms where CI can verify without holding signing capability.