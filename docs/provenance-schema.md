# Taviq Provenance Schema

Status: normative for Taviq Basic.

## Core semantics

Taviq records **observed AI involvement metadata**.

A provenance record does not mean that an AI generated all or any specific percentage of the code. It does not establish causality, productivity, authorship percentage, or vendor attestation.

Missing evidence is `Unknown`, not `Human-only`.

## 1. Runtime schema

Path:

```text
<git-dir>/taviq/runtime.json
```

Runtime metadata is ephemeral and lives inside the Git directory (per worktree), so it never appears as an untracked file and is never committed. It is written only in repositories enabled by `.taviq.yml`. It accumulates observations made before the next commit.

```json
{
  "schema_version": 2,
  "base_head": "<HEAD commit>",
  "observations": [
    {"tool": "claude", "mode": "agent", "model": "model-a", "role": "main"},
    {"tool": "claude", "mode": "agent", "model": "model-b", "role": "sub"},
    {"tool": "codex", "mode": "agent", "role": "main"}
  ]
}
```

Runtime stores one deduplicated set of observations and nothing else. Each observation is one `(tool, mode, model, role)` combination the integration exposed; a field the integration did not expose is omitted, never filled from another observation. The commit fields below (`tools`, `modes`, `models`, `agents`) are projections of this one set computed when the trailer is prepared, so they cannot disagree with each other.

Runtime schema version 1 stored the four projections as parallel lists. A version 1 file left by an older Taviq is still read for the rest of its window: its lists are merged into the projections as they are, without inventing tool/model/role associations they did not record.

Downgrading to an older Taviq in the middle of a window is not supported for the evidence already collected: an older binary does not read `observations`, so observations made before the downgrade are left out of that commit. The commit then records only what the older binary itself observed, or is Unknown. It never records evidence that was not observed.

The sections below define the projected fields, which are what commit trailers carry.

### tools

Type: set of strings.

Meaning: AI coding tools whose integration was observed during the current accumulation window.

Initial allowed values:

- `claude`
- `codex`
- `kiro`

Does not mean:

- percentage of code produced by each tool
- that every tool changed the final commit
- chronological order
- relative contribution

### modes

Type: set of strings.

Initial values:

- `assist` — AI assists an otherwise human-driven task
- `generate` — AI generates an artifact/change under direct instruction
- `agent` — an agent executes a broader engineering task
- `crew` — multiple cooperating agents execute the task
- `mixed` — mode cannot be represented by one observed category

Meaning: modes observed in the accumulation window.

Does not represent time share or contribution share.

### models

Type: set of strings.

Meaning: model identifiers explicitly exposed by the integration.

Model is optional. Taviq never guesses it.

Does not mean:

- which model produced which line/file
- relative contribution
- model quality

### agents

Type: optional set of strings, `<tool>:<role>` or `<tool>:<role>=<model>`.

Roles:

- `main` — the agent the developer runs
- `sub` — a subagent spawned by an agent

Meaning: which kind of agent was observed making a tool call, with that agent's model when the tool exposes it. An entry is written only when the tool itself reveals the role (for example, Claude Code and Codex set `agent_id` on hook events inside a subagent); otherwise no entry is written. A missing model is omitted, never filled with another agent's model.

Does not mean:

- which subagent was spawned by which main agent, or how many subagents ran
- that a subagent changed any file of the final commit
- relative contribution of main agents and subagents

`tools` and `models` remain the union over all observations, so readers that ignore `agents` see the same v1 meaning. Because all fields are projections of the same observations, every tool and model named in `agents` also appears in `tools` and `models`; that overlap is the v1-compatible summary, not independent evidence.

### accumulation

Sets are deduplicated. Order has no semantic meaning.

Example:

Claude/Model A → Codex/Model B → Claude/Model A

becomes:

```json
{
  "tools": ["claude", "codex"],
  "models": ["model-a", "model-b"]
}
```

not three usage events.

Basic intentionally records presence, not usage counts.

## 2. Commit provenance schema

Runtime observations are converted into durable Git commit trailers.

Proposed v1 multi-value representation:

```text
Taviq-Provenance: v1
Taviq-Tools: claude,codex
Taviq-Modes: agent
Taviq-Models: model-a,model-b
Taviq-Agents: claude:main=model-a,claude:sub=model-b
```

Rules:

- `Taviq-Provenance: v1` marks the commit as Recorded.
- Tools must contain at least one observed tool.
- Modes, Models and Agents are optional. `Taviq-Agents` is an optional field added within v1; readers that do not know it can ignore it.
- Values are deduplicated and serialized in stable lexical order.
- Unknown values are omitted.
- Empty fields are not written.
- Prompt, response, source, diff, token, credit, cost and identity are not part of Basic trailers.

### Recorded

A commit is `Recorded` when a supported Taviq provenance trailer exists with at least one tool.

Recorded does not mean cryptographically verified.

### Unknown

A commit is `Unknown` when Taviq has no usable provenance evidence.

Unknown does not mean Human-only.

## 3. PR aggregation schema

A PR aggregates commit provenance without converting overlapping sets into percentages.

Example:

```json
{
  "commits": 5,
  "recorded_commits": 4,
  "unknown_commits": 1,
  "coverage": 80.0,
  "tools": {
    "claude": 3,
    "codex": 2,
    "kiro": 1
  },
  "multi_tool_commits": 2
}
```

### coverage

```text
recorded commits / all commits in PR
```

A commit counts once even when multiple tools are recorded.

### tool counts

Tool counts are overlapping involvement counts.

For example:

```text
5 commits
Claude: 4
Codex: 2
```

does not mean 120% usage.

It means Claude was recorded on four commits and Codex on two, with at least one commit potentially containing both.

### multi_tool_commits

Number of commits containing more than one recorded tool.

The same principle applies to multiple modes, models and agents (`agents` counts each `<tool>:<role>[=<model>]` entry per commit).

## 4. Time/window semantics

Basic uses a repository-local accumulation window bounded by the Git `HEAD` observed by tool integrations.

Runtime stores `base_head` together with the observations.

- When another tool is observed and `HEAD` is unchanged, Taviq accumulates it into the same window.
- When a successful commit changes `HEAD`, the next tool observation detects the new `HEAD` and starts a fresh window.
- If a commit attempt fails, `HEAD` does not change, so the evidence is retained.
- Switching Claude → Codex → Kiro without a commit does not reset the window.

Runtime can also be explicitly cleared by deleting `<git-dir>/taviq/runtime.json`.

This is still an implementation boundary, not proof that every observed tool contributed to every file or line in the resulting commit.

A v1 commit record means:

> Taviq observed these tools/modes/models while the repository remained at the recorded pre-commit HEAD, before the trailer was prepared.

### Known limitations

- An external/manual commit that changes HEAD before another tool observation will cause the next observation to open a new window.
- Amend/rebase/reset operations can change HEAD without representing a simple new-work boundary.
- Multiple commits created without another AI-tool observation cannot be individually attributed from runtime state.

Stronger task/file/session correlation must use new fields or a schema version rather than silently strengthening v1 semantics.

## 5. Privacy boundary

Basic schema must not contain:

- prompt or response content
- source/diff content
- token/credit usage
- cost
- chat history
- developer identity
- productivity scores

## 6. Compatibility

Schema changes that alter field meaning require a schema/version change.

New optional fields may be added only when old readers can safely ignore them.

Taviq must not silently reinterpret existing v1 fields.
