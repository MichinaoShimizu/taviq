---
name: taviq-provenance
description: Preserve privacy-conscious AI engineering provenance while implementing, testing, reviewing, or committing software changes with an AI coding agent.
compatibility: Requires the taviq CLI/collector when deterministic event recording is enabled.
metadata:
  author: Taviq
  version: "0.1.0"
---

# Taviq Provenance

## Goal

Make AI-assisted engineering measurable without adding routine reporting work for developers. Provenance is an evidence input; it is not proof that AI caused an outcome.

## Privacy boundary

Never persist prompt text, assistant response text, source-code contents, diff contents, chat history, or individual productivity scores/rankings as provenance payloads.

Record only metadata the active tool/environment can reliably expose: tool/provider, model/version, interaction surface, execution environment, session ID, repository/worktree/branch, task/commit/PR IDs, file paths or hashes according to policy, usage/credits, actual or estimated cost, timestamps, provenance source, and confidence.

Unknown values remain unknown. Missing evidence is never proof of AI non-use.

## Execution lifecycle

1. When deterministic Taviq commands are available, open or resume a provenance session at the start of engineering work.
2. Let tool-native hooks or the collector observe metadata. Do not repeatedly ask the developer to report AI usage.
3. Around commit time, correlate the session with repository/worktree, touched files, task, and commit.
4. At task/session completion, close the provenance session and preserve only the minimal correlation required for later PR aggregation.
5. If recording is unavailable, continue the engineering task normally and leave provenance unknown. Never fabricate events.

## Measurement guardrails

Do not infer productivity improvement, time saved, ROI, quality improvement, customer value, business value, or causal claims from provenance alone.

Taviq combines provenance with human effort, work completion, quality, cost, product, and business data according to its Data Capability Model.

## Git behavior

Do not put detailed usage, token, credit, cost, prompts, or user information into commit messages. If the installed recorder requires a Git reference, use only the generated minimal provenance reference. Never invent an ID.

## Human agency

Do not interrupt normal development merely to collect optional metadata. Missing fields are preferable to guessed or burdensome collection. Do not use Taviq data to rank individuals.