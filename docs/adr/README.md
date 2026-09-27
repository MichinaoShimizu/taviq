# Taviq Architecture Decisions

These decisions are normative guardrails for contributors and AI coding agents.

## ADR-001 — Provenance first

Taviq is an AI Engineering Provenance Layer. Engineering KPI dashboards, ROI calculators, productivity scoring and executive analytics are not core responsibilities.

## ADR-002 — Recorded / Unknown

Basic uses two evidence states:

- Recorded: supported provenance metadata exists.
- Unknown: usable provenance evidence is absent.

Unknown must never be inferred as Human-only.

## ADR-003 — Zero-secret Basic

Basic must not require a Taviq-managed signing secret or proprietary key-management system.

Recorded does not mean cryptographically verified.

## ADR-004 — Zero-AI-overhead

Recording Basic provenance must not require an additional LLM/API call, token or AI credit.

Deterministic local processing and GitHub Actions are preferred.

## ADR-005 — Multi-value presence semantics

Tools, modes and models are sets of observed presence.

Counts are overlapping involvement counts, not usage percentages, contribution percentages, authorship percentages or time shares.

## ADR-006 — Git HEAD accumulation window

Basic v1 accumulates tool observations while Git HEAD remains unchanged. A changed HEAD starts a new window on the next tool observation.

This is an implementation boundary, not proof that every observed tool changed every file in the commit.

## ADR-007 — Privacy-minimal Basic

Basic must not store prompt/response content, source/diff content, token/credit usage, cost, chat history, developer identity or productivity scores in Git provenance.

## ADR-008 — Schema meaning is versioned

Existing v1 fields must not silently change meaning. Semantic changes require an explicit schema/version decision.


## ADR-009 — Organization-ready, server-optional core

Taviq Core must remain usable without a Taviq central server.

The architecture separates:

1. Developer installation / AI-tool integration.
2. Repository enablement and Git provenance.
3. Optional organization policy and rollout.
4. Optional forge integration such as GitHub PR summaries.

Organization adoption must not require copying the full Taviq implementation into every repository.

Repository provenance remains portable Git metadata rather than GitHub-only state.

## ADR-010 — Organization policy is not individual surveillance

Organization policy may define provenance enablement, supported tools, privacy constraints, schema compatibility and rollout requirements.

Basic provenance must not introduce developer productivity ranking, individual AI-usage scoring, or identity-based performance evaluation.

Organization reporting should default to repository / commit / PR evidence boundaries.

## ADR-011 — GitHub integration is optional

Commit provenance recording is Core functionality.

GitHub Actions, reusable workflows, Apps and Rulesets are optional integration/distribution mechanisms. Their absence must not prevent local Git provenance recording.


## ADR-012 — Hook execution location must not define provenance semantics

v0.1 may execute the commit hook from repository-local code.

Organization-ready distribution should move execution to a machine-installed or organization-managed Taviq CLI so repositories do not contain duplicated implementation.

Changing runner location must not silently change provenance schema or field semantics.


## ADR-013 — Go is the target implementation for distributable Taviq Core

Decision: Go is the implementation of Taviq Core. Python is not a Core runtime dependency.

Evidence from the Go Core spike:

- v1 provenance golden compatibility passes.
- multi-tool/mode/model set semantics pass.
- Git HEAD accumulation-window parity passes.
- init/deinit preserves existing `core.hooksPath`.
- doctor keeps GitHub Actions optional.
- Linux/macOS/Windows cross-builds succeed without third-party runtime dependencies.
- a built Linux binary passes `init → hook → doctor → deinit` in an external repository containing no Taviq source.
- binary size is roughly 3.0–3.3 MB.
- measured hook latency is roughly 2–3 ms, well below the 50 ms Basic budget.

Python was faster in the measured hook microbenchmark, so performance is not the reason for this decision.

The reason is distribution: a small self-contained binary materially simplifies developer and organization rollout compared with requiring Python/pip/pipx/venv management.

Migration rules:

- Do not silently change v1 provenance semantics.
- Keep Python as compatibility/reference until Go parity and AI-tool integrations are dogfooded.
- Remove repository-local Python fallback only after global binary distribution is proven in real use.
- GitHub integration remains optional and separate from Core.
