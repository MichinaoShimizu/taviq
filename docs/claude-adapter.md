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
