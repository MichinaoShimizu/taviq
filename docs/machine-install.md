# Machine-level Installation

Phase B defines installation state owned by the Taviq binary.

## State location

Taviq follows the user configuration directory convention exposed by the operating system. The Go implementation should use `os.UserConfigDir()` and store Taviq-owned state below a `taviq/` directory.

Examples include `~/.config/taviq/` on many Linux systems and the platform-appropriate user config directory on macOS/Windows.

## Ownership rule

Taviq may freely create, update and delete files inside its own config directory. It must not overwrite whole configuration files owned by Git, Claude, Codex, Kiro or other tools.

External integrations must be patched narrowly and reversibly, with enough state to remove only Taviq-owned entries.

## Machine lifecycle

- `taviq install`: create machine config and install supported global integrations.
- `taviq uninstall`: remove only Taviq-owned machine integrations/state.
- `taviq doctor`: report machine and repository readiness.
- `taviq init/deinit`: repository enablement only; eventually marker-only.

## Safety

- repeated install is idempotent
- uninstall restores or removes only Taviq-owned changes
- unrelated repositories remain unaffected
- absence of organization policy defaults to explicit repository opt-in
- machine install does not imply every repository is enabled
