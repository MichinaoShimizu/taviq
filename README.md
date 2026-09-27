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
Taviq-Agents: <optional>
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
taviq version
```

Repositoryを有効化（`.taviq.yml` markerのみ作成）:

```bash
taviq init
taviq doctor
```

解除:

```bash
taviq deinit
```

Git integrationとAI adapterはmachine-levelです。RepositoryにはTaviq実装やhookを置かず、`.taviq.yml`だけで有効化します。Organization policyによるzero-touch導入を次の目標としています。

## Supported tools

| Tool | Provenance |
| --- | --- |
| Claude Code | tool / mode / model / main・sub agent（`taviq install`で自動設定） |
| Codex | tool / mode / model / main・sub agent（`taviq install`で自動設定、初回のみ`/hooks`で承認） |
| Kiro | tool / mode（adapterのみ、自動設定は未対応） |
| Kiro Crew | tool=kiro / mode=crew（adapterのみ） |

取得できないmetadataは推測しません。

## Output examples

Commit messageの末尾に付くtrailerの例です（model名は説明用のplaceholder）。

Claude Code（main agentのみ）:

```text
Taviq-Provenance: v1
Taviq-Tools: claude
Taviq-Modes: agent
Taviq-Models: model-main
Taviq-Agents: claude:main=model-main
```

Claude Code（main agent + subagent）:

```text
Taviq-Provenance: v1
Taviq-Tools: claude
Taviq-Modes: agent
Taviq-Models: model-main,model-sub
Taviq-Agents: claude:main=model-main,claude:sub=model-sub
```

Claude Code（subagentのmodelを取得できなかった場合。main agentのmodelで埋めません）:

```text
Taviq-Provenance: v1
Taviq-Tools: claude
Taviq-Modes: agent
Taviq-Models: model-main
Taviq-Agents: claude:main=model-main,claude:sub
```

Claude Code + Codex（同じcommit windowで両方を観測）:

```text
Taviq-Provenance: v1
Taviq-Tools: claude,codex
Taviq-Modes: agent
Taviq-Models: gpt-model,model-main
Taviq-Agents: claude:main=model-main,codex:main=gpt-model
```

Kiro / Kiro Crew（modelとmain・subは取得できないため記録しません）:

```text
Taviq-Provenance: v1
Taviq-Tools: kiro
Taviq-Modes: crew
```

AI toolの関与を観測できなかったcommitにはtrailerを付けません。これはUnknownで、Human-onlyではありません。

各値はcommit window内で観測された集合で、順序・割合・貢献度を表しません。

## Privacy

Commit provenanceには低機密な最小metadataだけを残します。

保存しないもの:

- prompt / AI response
- source / diff本文
- token / credit / cost
- chat履歴
- developer identity
- productivity score

Claude Codeのmodelは、Claude Codeがlocalに書くtranscriptから`model`だけを読み取ります。transcriptの他の内容は保存しません。

## Design

- [Basic](docs/basic.md)
- [Provenance Schema](docs/provenance-schema.md)
- [Trust Model](docs/verified-provenance.md)
- [Target Architecture](docs/target-architecture.md)
- [Release Artifacts](docs/release.md)
- [Architecture Decisions](docs/adr/README.md)
- [Roadmap](docs/ROADMAP.md)

## Development

```bash
gofmt -w cmd/taviq
go test ./cmd/taviq
python3 scripts/lint_contract.py
python3 scripts/test_go_distribution_spike.py
```
