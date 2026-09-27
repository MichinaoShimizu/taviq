# Machine-level Git Integration

Taviq must not silently replace an existing global `core.hooksPath`.

## Initial safe strategy

`taviq install` may create a Taviq-owned hook directory under the machine config directory and configure global `core.hooksPath` only when no global hooksPath already exists or it already points to the Taviq-owned directory.

If another global hooksPath exists, installation fails visibly and leaves it unchanged. Chaining/interop is a separate design problem and must not be guessed.

## Dispatcher behavior

The machine-owned `prepare-commit-msg` hook invokes `taviq hook prepare-commit-msg`. The Go hook command checks repository enablement before recording provenance. A repository without a valid `.taviq.yml` marker is ignored.

## Uninstall

`taviq uninstall` removes global `core.hooksPath` only if it still points to the Taviq-owned directory. It never unsets or changes a value owned by another tool.
