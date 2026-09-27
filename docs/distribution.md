# Distribution Strategy

## Goal

Install Taviq once on a developer machine and expose a stable `taviq` command on `PATH`.

Repository enablement remains a separate operation:

```bash
taviq init
taviq doctor
taviq deinit
```

## v0.1

Repository-local scripts remain supported and are the compatibility fallback.

Do not publish a package that only installs the CLI wrapper while silently omitting its runtime modules.

## First global distribution target

Python package / isolated CLI installation is the first candidate because Taviq Basic is currently Python and requires no third-party runtime dependency.

Target user experience:

```bash
pipx install taviq
taviq --help
```

A later Homebrew or standalone binary may wrap the same CLI contract.

## Required package boundary

Before publishing, move runtime code from repository-relative `scripts/` loading into an importable package:

```text
src/taviq/
  cli.py
  installer.py
  doctor.py
  runtime.py
  hook.py
  provenance.py
```

Repository scripts may temporarily remain thin compatibility wrappers.

## Packaging acceptance criteria

A built/installed package must pass tests from outside the Taviq source checkout:

- `taviq --help`
- `taviq init`
- `taviq doctor --json`
- `taviq hook prepare-commit-msg`
- `taviq deinit`
- no import from repository-relative `scripts/`
- no network call for Basic provenance recording
- no secret requirement
- same v1 commit trailer semantics
- install/uninstall must not destroy existing Git hook configuration

## Organization distribution

Organization-managed installation may use MDM, developer bootstrap scripts, dev containers or other fleet tooling to install the same CLI.

Organization rollout must not require a different provenance schema.
