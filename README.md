# TAVIQ

**AI provenance for software development.**

Taviqは、**AIがどのソフトウェア変更に、どのように関与したかを自動で残すためのProvenance Layer**です。

Claude / Codex / Kiroなどを使った開発で、GitのHuman Authorだけでは分からない「変更がどう作られたか」を、commit / pull requestへ最小限の来歴として結び付けます。

> Git records who committed the change.  
> Taviq records how AI participated in the change.

## なぜ必要か

AI利用率、Token数、契約席数だけでは、AIが**どの実際の変更に関与したか**が分かりません。

一方、Gitには通常Human Authorは残りますが、

- Claudeが関与したのか
- Codexだったのか
- Kiroだったのか
- AssistなのかAgentなのか
- AI関与を確認できない変更がどれだけあるのか

は残りません。

このJoin Keyがなければ、将来Delivery・品質・コスト等とAI利用を結び付けようとしても、信頼できる分析の土台がありません。

Taviqはまず**分析する前の証拠を作ること**に集中します。

## Taviqがやること

```text
Claude / Codex / Kiro
        │
        │ workspace hook / integration
        ▼
minimal runtime metadata
        │
        │ prepare-commit-msg
        ▼
Git commit
  Taviq-Provenance: v1
  Taviq-Tool: claude
  Taviq-Mode: agent
  Taviq-Model: <optional>
        │
        ▼
GitHub Actions
        │
        ▼
Pull Request

AI provenance coverage  80%
Recorded                4 / 5 commits
Unknown                 1 commit
Tools                   Claude, Codex
```

**UnknownはHuman-onlyではありません。** 証拠がなければUnknownのまま扱います。

## Taviqがやらないこと

Taviqはprovenanceだけから、次を断定しません。

- AIで生産性が上がった
- AIで何時間削減できた
- AI ROIが高い
- 品質が改善した
- AIがDelivery改善の原因だった
- 個人Aは個人Bより生産的

Provenanceは「AI関与の証拠」であり、「AIが価値を生んだ証拠」ではありません。

## TaviqとKPI Playbookの責務

役割を明確に分けます。

**Taviq — 証拠を作る**

- AI tool / mode / model（取得できる場合）
- commit / PRとのcorrelation
- provenance coverage
- confirmed / unknown
- privacy-consciousな記録

**KPI Playbook — 証拠を読む**

- Delivery / Qualityとの組み合わせ
- KPI / counter metricの設計
- AI生産性の測定条件
- ROIや投資判断
- 因果と観測の区別

Taviqが将来分析用exportを提供することはあっても、プロダクトの中心責務はProvenanceです。

## 導入

```bash
python3 scripts/install_basic.py
```

repository-localのGit hookが設定されます。

通常どおりAIツールで開発してcommitしてください。対応integrationが一時metadataを設定し、commit時に最小Trailerへ変換します。

## 対応

| Tool | Integration |
| --- | --- |
| Claude Code | workspace SessionStart hook |
| Codex | workspace/plugin SessionStart hook + Skill fallback |
| Kiro | workspace Agent Spawn hook |

Modelは任意です。確実に取得できない場合は推測しません。

## Zero-AI-overhead by design

来歴記録のために追加のLLM推論を行いません。

| Overhead | Basicの設計 |
| --- | ---: |
| 追加AI API call | **0** |
| 追加AI token | **0** |
| 追加AI credit | **0** |
| 開発者の都度入力 | **0** |
| Local hook latency | **50ms未満を目標** |
| Git metadata | **1KB未満 / commitを目標** |

Latency等は環境依存なのでCI / dogfoodで継続測定します。

## Privacy

Gitに残すのは低機密な最小metadataだけです。

```text
Taviq-Provenance: v1
Taviq-Tool: claude
Taviq-Mode: agent
Taviq-Model: <optional>
```

デフォルトでは以下をGitへ残しません。

- Prompt / AI Response
- Source / Diff本文
- Token / Credit
- Cost
- Chat履歴
- Human effort
- 個人生産性スコア

## 何ができるようになるか

Taviq単体:

- PR/commitにAI関与の明示的な来歴を残す
- Claude / Codex / Kiro等のtoolを識別
- Agent等のmodeを識別
- provenance coverageを把握
- AI関与を確認できない変更をUnknownとして把握
- 将来の分析や運用ポリシーと結び付けられるJoin Keyを作る

他データと組み合わせる場合:

```text
Taviq Provenance + Git/CI       → AI関与変更のDelivery/検証傾向
Taviq Provenance + Quality      → AI関与変更の品質傾向
Taviq Provenance + Human Effort → 確認・修正負荷
Taviq Provenance + Cost         → 投資分析の入力
```

これらの組み合わせから因果を自動的に断定しません。

## 設計ドキュメント

- [Basic setup](docs/basic.md)
- [Provenance Trust Model](docs/verified-provenance.md)
- [Data Capability Model](docs/data-capability-model.md)
- [Deployment Modes](docs/deployment-modes.md)
- [Implementation Roadmap](docs/ROADMAP.md)

## 現在の方針

Taviqは当面、**AI Engineering Provenance Layer** に集中します。

過去に作成したDelivery / ROI / Collector / Relay等の実験は、Provenanceの利用可能性を検証したものです。現行Basicの仕様ではありません。今後の新規開発優先度はProvenance Basicの正確性、対応ツール、導入容易性、privacy、overhead、監査可能性を最優先とします。

## Historical / experimental code

リポジトリには、Provenance専用へ方針転換する前に作成したDelivery / ROI / Collector / Relayの実験コード・文書が一部残っています。これらは**現行Taviq Basicの導入経路ではありません**。

現行の正本は README、[Basic setup](docs/basic.md)、[Deployment Modes](docs/deployment-modes.md)、[Provenance Trust Model](docs/verified-provenance.md)、[Roadmap](docs/ROADMAP.md) です。
