> **Historical / experimental.** This document describes an earlier Collector/Analytics design and is not the current Taviq Basic architecture. Current Basic is zero-server and records minimal provenance through Git trailers and GitHub Actions. See [README](../README.md), [Basic](basic.md), and [Roadmap](ROADMAP.md).

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


## GitHub artifact transport decision

GitHub Actions artifacts are produced by workflow runs. GitHub's public Actions artifact REST endpoints support listing, retrieving, downloading and deleting artifacts, but are not a general external-client upload API.

Triggering a workflow externally through workflow_dispatch is possible, but requires Actions write permission. Taviq does not require that permission from the local collector merely to move provenance metadata.

Therefore:

- Local Collector does **not** dispatch GitHub workflows.
- Local Collector does **not** request Actions write permission.
- GitHub artifact transport is not the primary Local → GitHub handoff.
- The next transport implementation is a local/self-hosted relay with an explicit endpoint and narrow write-only ingestion contract.
- GitHub Actions remains a read/aggregation/presentation layer once evidence is available to it through an approved integration.

This preserves least privilege and keeps transport replaceable.
