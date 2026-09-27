# Organization-ready Architecture

## Layers

```text
Developer machine
  Taviq CLI + AI tool integrations
              |
              v
Repository
  enablement + Git provenance
              |
              +--------------------+
              |                    |
              v                    v
Optional organization policy   Optional forge integration
privacy / tools / schema       GitHub PR summary / workflow / App
```

## Core requirement

A repository must be able to record Taviq provenance without:

- a Taviq server
- a GitHub Action
- a Taviq-managed secret
- an additional AI call

Git is the durable provenance substrate.

## Developer installation

Target UX:

```bash
taviq install
```

Installed once on a developer machine. It provides the CLI and supported AI-tool integrations.

## Repository enablement

Target UX:

```bash
taviq init
taviq doctor
taviq deinit
```

Repository enablement should be small and reversible. The full implementation should not be copied into every repository.

## Organization policy

An organization may publish policy such as:

```yaml
schema_version: 1
provenance:
  enabled: true
tools:
  allowed:
    - claude
    - codex
    - kiro
privacy:
  prompt: forbidden
  response: forbidden
  source: forbidden
  developer_identity: forbidden
```

Policy defines collection boundaries and compatibility. It does not convert provenance into productivity scoring.

## GitHub

GitHub is an optional distribution and presentation layer.

Possible organization mechanisms:

- reusable workflow for PR aggregation
- repository rulesets for required Quality Gate
- GitHub App for future zero-touch rollout

The provenance record itself remains in Git commit metadata.

## Organization reporting boundary

Default aggregation dimensions should be:

- organization
- repository
- pull request
- commit
- tool / mode / model presence where available

Developer ranking and individual productivity scoring are out of core scope.

## v0.1 compatibility

v0.1 remains repository-local Basic. Organization-ready work must not delay Basic dogfood/release unless a v0.1 choice would make organization rollout materially harder later.
