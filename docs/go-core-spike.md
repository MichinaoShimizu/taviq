# Go Core Spike Results

Status: evaluation in progress.

## CI measurement

Environment: GitHub-hosted Ubuntu runner.

| Metric | Go spike | Python Basic |
| --- | ---: | ---: |
| Hook median | 2.68 ms | 1.43 ms |
| Hook p95 | 3.00 ms | not currently reported |
| Binary size | 3,149,781 bytes (~3.15 MB) | requires Python runtime |
| Metadata example | same v1 schema | 60 bytes in benchmark |

Both implementations are far below the Basic local-hook latency target of 50 ms.

## Interpretation

The current evidence does **not** justify Go on hook speed: Python was faster in this CI sample.

The case for Go is distribution and organization operations:

- one self-contained binary
- no Python/pip/pipx runtime requirement for end users
- straightforward MDM/bootstrap distribution
- predictable cross-platform artifact
- no third-party runtime dependencies

## Compatibility demonstrated so far

Go spike tests cover:

- v1 commit trailer golden compatibility
- multi-tool/mode/model stable ordering
- init/deinit hooksPath restoration
- repeated init preserving original hooksPath
- doctor Core readiness
- GitHub Actions remaining optional

## Remaining decision evidence

Before adopting Go as Core:

- cross-compile macOS arm64/amd64
- cross-compile Linux arm64/amd64
- cross-compile Windows amd64
- test built binary outside source checkout
- confirm runtime accumulation parity
- confirm Claude/Codex/Kiro integration strategy with global binary
- compare maintenance complexity

Do not remove Python until these checks pass.
