# Machine-level AI Integrations

Taviq AI-tool integrations are machine-level adapters whose only responsibility is to emit provenance observations to the installed binary.

Canonical adapter command: `taviq observe <tool> <mode> [model]`.

## Ownership

Taviq owns only files under its machine config directory. It must not replace an AI tool's complete user configuration.

The first implementation generates adapter artifacts under `<user-config>/taviq/integrations/`. Adapter names carry a `taviq-` prefix so that the directory never shadows the real `claude`, `codex` or `kiro` commands if placed on `PATH`, and they invoke the binary by the absolute path resolved at install time. Tool-specific installation into Codex/Kiro configuration is a separate step after each supported configuration contract is verified.

## Adapter artifacts

- `taviq-claude` invokes `taviq observe claude agent`
- `taviq-codex` invokes `taviq observe codex agent`
- `taviq-kiro` invokes `taviq observe kiro agent`
- `taviq-kiro-crew` invokes `taviq observe kiro crew`
- model is omitted unless the tool supplies a trustworthy value

`taviq observe` records nothing in a repository without a valid `.taviq.yml` marker.

Adapters must remain tiny, deterministic, secret-free, and reversible.

## Claude Code

`taviq install` adds one `PreToolUse` hook to the Claude Code user settings (`$CLAUDE_CONFIG_DIR/settings.json`, default `~/.claude/settings.json`):

    {"matcher": "Edit|MultiEdit|Write|NotebookEdit|Bash",
     "hooks": [{"type": "command", "command": "'<taviq>' hook claude-code"}]}

- Only file edits and Bash are matched. Bash runs before a `git commit` Claude makes itself, so a second commit in the same session is observed even after the first commit reset the observation.
- `taviq hook claude-code` reads only `cwd` from the hook event on stdin and records `claude` / `agent` there. The model is not recorded because the event does not carry a trustworthy value.
- The hook never prints and always exits 0, so it cannot block or alter a Claude tool call. Outside an enabled repository it does nothing.
- Install is skipped when the Claude config directory does not exist, and fails visibly without writing when the settings file is not valid JSON.
- Other settings and hooks are preserved. The file is rewritten atomically with its permissions kept; key order may change.
- Taviq-owned entries are identified by a command ending in `hook claude-code`. `taviq uninstall` removes only those, and `taviq doctor` reports them as `claude_code_hook`.

Re-run `taviq install` after moving the binary.
