# Provenance Envelope

Local raw events remain local. Taviq exports only a minimal envelope when CI/PR aggregation needs evidence.

The envelope intentionally excludes:

- prompt / response / chat
- source code / diff
- token / credit usage
- cost
- raw timestamps and tool event payloads
- developer identity

It may contain:

- pseudonymous session reference
- repository / branch / commit correlation
- tool / mode / model when available
- explicit provenance-confirmed file paths, or SHA-256 path hashes

Path hashing is optional. Plain paths allow GitHub Actions to calculate file-level coverage directly. Hashed paths require the GitHub integration to hash the PR changed-file list using the same representation before comparison.

The envelope is a transport artifact, not a productivity record. It should be generated explicitly by Taviq tooling and can be deleted after PR aggregation.
