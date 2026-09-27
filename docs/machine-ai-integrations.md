# Machine-level AI Integrations

Taviq AI-tool integrations are machine-level adapters whose only responsibility is to emit provenance observations to the installed binary.

Canonical adapter command: `taviq observe <tool> <mode> [model]`.

## Ownership

Taviq owns only files under its machine config directory. It must not replace an AI tool's complete user configuration.

The first implementation generates adapter artifacts under `<user-config>/taviq/integrations/`. Adapter names carry a `taviq-` prefix so that the directory never shadows the real `claude`, `codex` or `kiro` commands if placed on `PATH`, and they invoke the binary by the absolute path resolved at install time. Tool-specific installation into Claude/Codex/Kiro configuration is a separate step after each supported configuration contract is verified.

## Adapter artifacts

- `taviq-claude` invokes `taviq observe claude agent`
- `taviq-codex` invokes `taviq observe codex agent`
- `taviq-kiro` invokes `taviq observe kiro agent`
- `taviq-kiro-crew` invokes `taviq observe kiro crew`
- model is omitted unless the tool supplies a trustworthy value

`taviq observe` records nothing in a repository without a valid `.taviq.yml` marker.

Adapters must remain tiny, deterministic, secret-free, and reversible.