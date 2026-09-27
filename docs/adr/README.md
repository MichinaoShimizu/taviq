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
