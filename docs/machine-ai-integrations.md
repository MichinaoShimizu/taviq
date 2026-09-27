# Machine-level AI Integrations

Taviq AI-tool integrations are machine-level adapters whose only responsibility is to emit provenance observations to the installed binary.

Canonical adapter command: `taviq observe <tool> <mode> [model]`.

## Ownership

Taviq owns only files under its machine config directory. It must not replace an AI tool's complete user configuration.

The first implementation generates adapter artifacts under `<user-config>/taviq/integrations/`. Adapter names carry a `taviq-` prefix so that the directory never shadows the real `claude`, `codex` or `kiro` commands if placed on `PATH`, and they invoke the binary by the absolute path resolved at install time. Tool-specific installation into Kiro configuration is a separate step after its configuration contract is verified.

## Adapter artifacts

- `taviq-claude` invokes `taviq observe claude agent`
- `taviq-codex` invokes `taviq observe codex agent`
- `taviq-kiro` invokes `taviq observe kiro agent`
- `taviq-kiro-crew` invokes `taviq observe kiro crew`
- model is omitted unless the tool supplies a trustworthy value

`taviq observe` records nothing in a repository without a valid `.taviq.yml` marker.

Adapters must remain tiny, deterministic, secret-free, and reversible.

## Claude Code and Codex

`taviq install` adds one `PreToolUse` hook to each tool's user-level hooks file, when that tool's config directory exists:

| Tool | File | Matcher | Hook command |
| --- | --- | --- | --- |
| Claude Code | `$CLAUDE_CONFIG_DIR/settings.json` (default `~/.claude/settings.json`) | `Edit\|MultiEdit\|Write\|NotebookEdit\|Bash` | `'<taviq>' hook claude-code` |
| Codex | `$CODEX_HOME/hooks.json` (default `~/.codex/hooks.json`) | `^(Bash\|apply_patch\|Edit\|Write)$` | `'<taviq>' hook codex` |

Both files share the `{"hooks": {"PreToolUse": [{"matcher", "hooks": [...]}]}}` shape.

- Only file edits and shell commands are matched. The shell hook runs before a `git commit` the agent makes itself, so a second commit in the same session is observed even after the first commit reset the observation.
- `taviq hook <tool>` reads `cwd` from the event on stdin and records `<tool>` / `agent` there.
- Model: Codex supplies `model` in the event, so it is recorded when it is a plain identifier (`[A-Za-z0-9._:/@+-]`, at most 128 characters); anything else is dropped. Claude Code events do not carry a model, so none is recorded.
- The hook never prints and always exits 0, so it cannot block or alter a tool call. Outside an enabled repository it does nothing.
- Install is skipped for a tool whose config directory does not exist, and fails visibly without writing when the file is not valid JSON or has an unexpected `hooks` shape.
- Other settings and hooks are preserved. The file is rewritten atomically with its permissions kept; key order may change.
- Taviq-owned entries are identified by the hook command suffix. `taviq uninstall` removes only those, and `taviq doctor` reports them as `claude_code_hook` / `codex_hook`.
- Codex runs a non-managed hook only after the user trusts it once in `/hooks`. Taviq does not write Codex trust state, which has no supported interface.

Re-run `taviq install` after moving the binary.

## Kiro

Kiro supports user-level hooks in `~/.kiro/hooks/`, but the documented trigger names differ between Kiro pages and versions. Taviq does not install a Kiro hook until the contract is verified against a released Kiro version; the `taviq-kiro` and `taviq-kiro-crew` adapters remain available.
