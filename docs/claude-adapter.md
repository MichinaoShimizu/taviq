# Claude Code adapter (MVP)

This adapter is intentionally schema-tolerant and privacy-minimal.

## What it records

Only allow-listed metadata exposed to the hook, plus Git context discovered locally:

- session/event identifier
- model name when exposed
- numeric usage counters when exposed
- repository/worktree/branch/current commit
- timestamp
- provenance source/confidence

## What it drops

Prompt, response, messages/content, tool input/output, source code and diffs are not allow-listed and therefore are not persisted.

## Hook wiring

Configure Claude Code hooks to pipe their JSON event payload to:

```bash
python3 adapters/claude/hook.py
```

Use lifecycle hooks available in the installed Claude Code version (for example session/tool/stop events where supported). Taviq does not depend on undocumented fields: unknown fields are ignored and unavailable fields remain unknown.

Events are appended to:

```text
~/.taviq/events/YYYY-MM-DD.jsonl
```

Override with `TAVIQ_HOME` for tests or organization policy.

## Git correlation

For every received event the collector resolves, when available:

- repository/worktree
- current branch
- current HEAD

File-level and commit/PR correlation are the next layer; this MVP deliberately does not inspect diff/source contents.


## PR provenance coverage

Taviq can aggregate explicit session file evidence against the changed-file list supplied by the GitHub integration.

Example:

```text
Taviq AI Provenance

Coverage     66.7%
Confirmed    2 / 3 files
Unknown      1 file
```

Coverage is the share of changed files for which Taviq has provenance evidence. It is **not** the share of code written by AI.

Unknown files are never classified as human-only merely because no AI event was observed.

The core collector produces a GitHub-Check-ready summary, but publishing a Check Run is intentionally kept in the GitHub integration layer so the local collector does not require repository write credentials.
