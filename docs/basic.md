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
python3 scripts/install_basic.py install
```

This configures the repository-local Git hook path to `.taviq/hooks` and remembers the previous `core.hooksPath` so it can be restored.\n\nUninstall:\n\n```bash\npython3 scripts/install_basic.py uninstall\n```

## AI execution metadata

Tool integrations accumulate observed metadata in `.taviq/runtime.json`.

Multiple tools, modes and models may be observed before one commit. Duplicate values are removed. Environment variables remain a backward-compatible fallback.

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
| Claude Code | workspace SessionStart hook | optional; never guessed |
| Codex | workspace/plugin SessionStart hook; Skill remains a fallback | optional; never guessed |
| Kiro | workspace Agent Spawn hook | optional; never guessed |

Basic v0.1 requires tool provenance, not model provenance. Model is enrichment only. Multiple tools/models in one commit represent observed presence, not contribution percentages or chronological order. See [Provenance Schema](provenance-schema.md).

## Dogfood acceptance test

1. AI tool starts work in the repository.
2. `.taviq/runtime.json` is created without developer input.
3. A normal Git commit receives the minimal Taviq trailer.
4. The runtime file is not committed.
5. A pull request triggers the Taviq Basic Provenance workflow.
6. The Actions summary reports the commit as recorded and identifies all observed tools.
7. No prompt, response, code, token, cost, or developer identity appears in the trailer or summary.