# Taviq Basic

Taviq Basic is the default, serverless deployment.

## Flow

```text
AI coding tool
  → minimal commit trailer
  → git push
  → GitHub Actions
  → PR provenance summary
```

## Install in a repository

Taviq Core is a self-contained Go binary.

Once `taviq` is available on `PATH`, enable a repository with:

```bash
taviq init
taviq doctor
```

Remove repository enablement with:

```bash
taviq deinit
```

`init` creates only the declarative `.taviq.yml` marker. `deinit` removes that marker and transient runtime state. Repository-local hook files are not installed; commit integration is machine-level.

GitHub Actions are optional and are not required for commit provenance recording.

## AI execution metadata

Tool integrations accumulate observed metadata in `<git-dir>/taviq/runtime.json`, only in enabled repositories.

Multiple tools, modes and models may be observed before one commit. Runtime keeps one deduplicated set of observations; the trailer fields are derived from it. Environment variables remain a backward-compatible fallback.

The resulting commit message uses the v1 multi-value schema:

```text
Taviq-Provenance: v1
Taviq-Tools: claude,codex
Taviq-Modes: agent
Taviq-Models: model-a,model-b
```

Only Tools are required. Modes and Models are optional and never guessed.

The hook is idempotent and does not duplicate an existing Taviq provenance trailer.

## Privacy

Basic does not put prompts, responses, source code, diffs, token/credit usage, cost, or developer identity into Git.

## GitHub

The `Taviq Basic Provenance` workflow reads commit trailers on pull requests and publishes:

- commit provenance coverage
- recorded / unknown commit counts
- observed tools
- observed modes
- observed models

Unknown commits are not treated as human-only.

## Limitation

Basic records only explicit commit provenance. It does not calculate AI ROI, human time saved, quality impact, or causal effect. Those require additional data sources.

## Supported Basic integrations

| Tool | Automatic Basic metadata | Model |
| --- | --- | --- |
| Claude Code | machine-level `PreToolUse` hook installed by `taviq install` | not recorded |
| Codex | machine-level `PreToolUse` hook installed by `taviq install` (trusted once via `/hooks`) | recorded when Codex supplies it |
| Kiro | not wired yet; `taviq observe kiro <mode>` adapter only | optional; never guessed |

Basic v0.1 requires tool provenance, not model provenance. Model is enrichment only. Multiple tools/models in one commit represent observed presence, not contribution percentages or chronological order. See [Provenance Schema](provenance-schema.md).

## Dogfood acceptance test

1. AI tool edits a file or runs a command in the repository.
2. `<git-dir>/taviq/runtime.json` is created without developer input.
3. A normal Git commit receives the minimal Taviq trailer.
4. The runtime file is not committed.
5. A pull request triggers the Taviq Basic Provenance workflow.
6. The Actions summary reports the commit as recorded and identifies all observed tools.
7. No prompt, response, code, token, cost, or developer identity appears in the trailer or summary.