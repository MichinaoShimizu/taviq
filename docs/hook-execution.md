# Hook Execution

Taviq Core is executed by the installed `taviq` binary.

```text
Git prepare-commit-msg
        |
        v
taviq hook prepare-commit-msg <message-file>
        |
        v
Go Core
```

Repository initialization installs only the Git hook/configuration needed to invoke the binary. The Taviq Core implementation is not copied into each repository.

## Compatibility requirement

Execution location and distribution method must not change v1 provenance semantics.

The same schema applies whether the binary was installed manually, by a package manager, or by organization-managed fleet tooling.

There is no Python Core fallback. If the `taviq` binary is unavailable, the hook must fail visibly rather than silently record misleading provenance.
