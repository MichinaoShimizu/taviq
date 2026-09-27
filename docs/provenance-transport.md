# Provenance Transport

## Decision

Taviq does not use commit messages or tracked repository files as the primary transport for provenance envelopes.

The transport layer is replaceable:

1. **Local / CI artifact transport** for MVP and dogfooding.
2. **Self-hosted endpoint** for organizations that need central aggregation without Taviq Cloud.
3. **Taviq Cloud endpoint** only when explicitly enabled.

## Artifact transport

A producer exports one or more minimal envelopes into a temporary directory.

Example:

```text
.taviq-out/
  envelopes/
    <session-ref>.json
```

A CI workflow may upload this directory as a short-lived artifact. A downstream PR aggregation job downloads envelopes associated with the relevant commit/run and compares their explicit file evidence with the PR changed-file list.

The artifact must not contain raw event files.

### Artifact payload allowed

- schema version
- pseudonymous session reference
- repository / branch / commit correlation
- tool / mode / model when exposed
- explicit observed paths or path hashes

### Artifact payload forbidden

- prompt / response
- source or diff contents
- raw hook payload
- token / credit usage
- cost
- developer identity

## Retention

Artifacts are transport, not the analytics database. Configure the shortest practical retention supported by the CI environment and delete/expire them after aggregation.

## Trust

An artifact proves only that a Taviq producer emitted an envelope. Later phases should add signing/attestation so the aggregator can distinguish trusted collectors from arbitrary files.

Until signing is implemented, UI must label artifact-derived provenance as collector evidence, not cryptographically verified evidence.
