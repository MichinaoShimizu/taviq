# Hook Execution Boundary

## Current v0.1

Repository initialization installs a repository-local `prepare-commit-msg` hook.

The current implementation executes the repository-local Basic writer. This keeps v0.1 self-contained while distribution is still repository-based.

## Target distribution

Organization-ready distribution should allow the hook to call an installed Taviq CLI instead:

```text
Git prepare-commit-msg
        |
        v
taviq hook prepare-commit-msg <message-file>
        |
        v
installed Taviq runtime
```

This removes the requirement to copy the Taviq implementation into every repository.

## Compatibility requirement

The provenance schema and commit trailer semantics must be identical regardless of runner location:

- repository-local runner
- machine-installed CLI
- organization-managed CLI

Distribution location must not change v1 provenance meaning.

## Migration rule

v0.1 keeps the repository-local runner as the default.

A machine-installed runner must be introduced as an explicit capability and dogfooded before repository-local execution is removed.

Repository configuration should contain only enablement/policy state, not a duplicated implementation.


## Transitional runner selection

Repository initialization may install a compatibility hook that selects execution in this order:

1. If `taviq` is available on `PATH`, run `taviq hook prepare-commit-msg`.
2. Otherwise use the repository-local v0.1 writer.

This allows machine/organization-managed installations to be dogfooded without breaking repositories that still depend on the v0.1 local implementation.

The fallback can be removed only after global distribution is independently proven reliable.
