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

```bash
python3 scripts/install_basic.py
```

This configures the repository-local Git hook path to `.taviq/hooks`.

## AI execution metadata

The agent/tool integration sets:

```bash
TAVIQ_TOOL=claude
TAVIQ_MODE=agent
TAVIQ_MODEL=<optional model id>
```

Only `TAVIQ_TOOL` is required. If no tool is known, the hook writes nothing and the commit remains unknown.

The resulting commit message contains only:

```text
Taviq-Provenance: v1
Taviq-Tool: claude
Taviq-Mode: agent
Taviq-Model: <only when known>
```

The hook is idempotent and does not duplicate existing Taviq trailers.

## Privacy

Basic does not put prompts, responses, source code, diffs, token/credit usage, cost, or developer identity into Git.

## GitHub

The `Taviq Basic Provenance` workflow reads commit trailers on pull requests and publishes:

- commit provenance coverage
- confirmed / unknown commit counts
- observed tools
- observed modes
- observed models

Unknown commits are not treated as human-only.

## Limitation

Basic proves only explicit commit provenance. It does not calculate AI ROI, human time saved, quality impact, or causal effect. Those require additional data sources.
