# Release Artifacts

Phase A defines how a Taviq Core binary identifies itself and how release binaries are produced.

## Version

`taviq version` (or `taviq --version`) prints `taviq <version>`. `taviq doctor` includes the same value as `version`, so fleet tooling can read it without a separate call.

The version is resolved in this order:

1. the release tag stamped at build time with `-ldflags "-X main.version=<tag>"`
2. the module version of a binary built with `go install github.com/MichinaoShimizu/taviq/cmd/taviq@<tag>`
3. `dev` for any other local build

A `dev` binary is never a release.

## Building a release

    python3 scripts/build_release.py v0.1.0

The script writes to `dist/` (ignored by Git):

- `taviq-<version>-<os>-<arch>[.exe]` for linux/amd64, linux/arm64, darwin/amd64, darwin/arm64 and windows/amd64
- `SHA256SUMS` in `sha256sum -c` format

Binaries are built with `CGO_ENABLED=0 -trimpath -ldflags "-s -w"`. The script fails unless the host binary reports exactly the requested version. Versions must follow `vMAJOR.MINOR.PATCH` with an optional pre-release suffix such as `-rc.1`.

## Verifying a download

    sha256sum -c SHA256SUMS --ignore-missing

## Not yet decided

- binary signing (Sigstore / platform code signing), evaluated from need per the [Trust Model](verified-provenance.md)
- publishing releases from CI
- Homebrew / Windows / Linux package distribution
