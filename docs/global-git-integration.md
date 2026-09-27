# Machine-level Git Integration

Taviq must not silently replace an existing global `core.hooksPath`.

## Initial safe strategy

`taviq install` may create a Taviq-owned hook directory under the machine config directory and configure global `core.hooksPath` only when no global hooksPath already exists or it already points to the Taviq-owned directory.

If another global hooksPath exists, installation fails visibly and leaves it unchanged. Chaining/interop is a separate design problem and must not be guessed.

## Dispatcher behavior

The machine-owned `prepare-commit-msg` hook invokes `taviq hook prepare-commit-msg` by the absolute binary path resolved at install time, so Git clients with a reduced `PATH` still reach it. Re-run `taviq install` after moving the binary. The Go hook command checks repository enablement before recording provenance. A repository without a valid `.taviq.yml` marker is ignored.

Trailers are added with `git interpret-trailers`, so they land in the trailer block before comment lines and a verbose diff. An existing `Taviq-Provenance` trailer is detected from the parsed trailer block only.

## Repository hooks are preserved

A global `core.hooksPath` replaces `$GIT_DIR/hooks` in every repository, enabled or not. To keep unrelated repositories unaffected, the Taviq hook directory contains a shim for each common client-side hook that runs the repository's own `<git-common-dir>/hooks/<name>` when it is executable, with the same arguments, stdin and exit status. `prepare-commit-msg` runs the repository hook first, then Taviq.

High-frequency hooks (`reference-transaction`, `post-index-change`) are not chained, to keep overhead off every ref and index update. A repository relying on them needs its own `core.hooksPath`.

## Repository-level hooksPath

A repository-level `core.hooksPath` (husky, lefthook, ...) takes precedence over the global value, so the Taviq hook does not run there. `taviq doctor` reports this as `no_repository_hooks_path: false` and not ready. Chaining into such tools is a separate design problem.

## Uninstall

`taviq uninstall` removes global `core.hooksPath` only if it still points to the Taviq-owned directory. It never unsets or changes a value owned by another tool.
