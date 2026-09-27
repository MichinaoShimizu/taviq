# Machine-level AI Integrations

Taviq AI-tool integrations are machine-level adapters whose only responsibility is to emit provenance observations to the installed binary.

Canonical adapter command: `taviq observe <tool> <mode> [model]`.

## Ownership

Taviq owns only files under its machine config directory. It must not replace an AI tool's complete user configuration.

The first implementation generates adapter artifacts under `<user-config>/taviq/integrations/`. Tool-specific installation into Claude/Codex/Kiro configuration is a separate step after each supported configuration contract is verified.

## Adapter artifacts

- Claude adapter invokes `taviq observe claude agent`
- Codex adapter invokes `taviq observe codex agent`
- Kiro adapter invokes `taviq observe kiro agent`
- Kiro Crew adapter invokes `taviq observe kiro crew`
- model is omitted unless the tool supplies a trustworthy value

Adapters must remain tiny, deterministic, secret-free, and reversible.