# TAVIQ

**AI provenance for software development.**

Taviqは、Claude / Codex / KiroなどのAI coding toolがソフトウェア変更に関与した事実を、Git commitへ最小限のprovenanceとして記録するツールです。

```text
AI tool
  ↓
taviq observe
  ↓
Git commit

Taviq-Provenance: v1
Taviq-Tools: claude,codex
Taviq-Modes: agent
Taviq-Models: <optional>
```

UnknownはHuman-onlyを意味しません。証拠がなければUnknownとして扱います。

## Core

Taviq CoreはGo製の単一binaryです。

- server不要
- secret不要
- 追加AI API call / token / credit不要
- GitHub Actions不要
- prompt / response / source / diffをGitへ保存しない
- developer productivity scoreを作らない

GitHub等のPR集約はOptional integrationです。

## Install

現在はsourceからbuildできます。

```bash
go build -o taviq ./cmd/taviq
install -m 0755 ./taviq ~/.local/bin/taviq
taviq install
```

Repositoryを有効化:

```bash
taviq init
taviq doctor
```

解除:

```bash
taviq deinit
```

Target architectureではmachine-level installとorganization policyにより、repositoryへTaviq実装を置かずzero-touch導入できる形を目指します。

## Supported tools

| Tool | Provenance |
| --- | --- |
| Claude Code | tool / mode / optional model |
| Codex | tool / mode / optional model |
| Kiro | tool / mode / optional model |

取得できないmetadataは推測しません。

## Privacy

Commit provenanceには低機密な最小metadataだけを残します。

保存しないもの:

- prompt / AI response
- source / diff本文
- token / credit / cost
- chat履歴
- developer identity
- productivity score

## Design

- [Basic](docs/basic.md)
- [Provenance Schema](docs/provenance-schema.md)
- [Trust Model](docs/verified-provenance.md)
- [Target Architecture](docs/target-architecture.md)
- [Architecture Decisions](docs/adr/README.md)
- [Roadmap](docs/ROADMAP.md)

## Development

```bash
gofmt -w cmd/taviq
go test ./cmd/taviq
python3 scripts/lint_contract.py
python3 scripts/test_go_distribution_spike.py
```
