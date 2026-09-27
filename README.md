# TAVIQ

**Engineering Intelligence for Decisions**

デリバリー · 品質 · AI · ROI

Taviqは、開発組織のデータを「数値 → 何を意味するか → なぜ重要か → 次に何を判断するか」へ変換し、経営層と開発組織の意思決定を支援するプロダクトです。

## レポートの考え方

Taviqは、読み手の意思決定レベルに応じてレポートを3層に分けます。

1. **経営層** — 投資、創出されたキャパシティ、デリバリー、品質、事業成果との接続、必要な経営判断。
2. **開発組織長 / EM** — サイクルタイム、レビュー待ち、AI ROI、AI関与あり・なしの観測比較など。
3. **診断詳細** — 上位指標が動いた理由を調べるための、リポジトリ別PR件数・サイズ・サイクル・レビュー指標。

PR件数やレビュー待ち時間は診断材料であり、経営成果そのものとしては扱いません。

経営層向けの各指標は、次の4点を必ず示します：

`数値 → 何を意味する？ → なぜ重要？ → 次の判断`

AI reporting follows the same chain. Adoption, generated-code share, or token usage are not treated as business outcomes.

## What it measures

- Delivery: PR throughput, merge cycle time, first-review wait, PR size, long review waits
- Generative AI: net human time saved, capacity value, program cost, estimated ROI
- AI delivery comparison: AI-involved vs non-AI changes with provenance coverage
- Guardrails: metrics describe the delivery system, not individual performance; observational comparisons are not causal estimates

## 設計原則

Taviqが「何を言えるか」は、接続されたデータによって決まります。GitHubだけからAI ROIや事業成果を推測しません。

単体データ・複数データの組み合わせ・AI価値の5段階・Evidence Level・不足データの扱いは [Data Capability Model](docs/data-capability-model.md) を正本とします。

## AI来歴（Provenance）

Taviq Basicは、Claude / Codex / Kiroを使った開発の来歴を、サーバーなしでGitHubへ残せるようにします。

目的は「誰がAIを多く使ったか」を監視することではありません。**どの変更に、どのAIツール・利用モードの関与が明示的に確認できたか**を記録し、後からDelivery・品質・AI投資分析へ接続できる証拠を作ります。

### Basicアーキテクチャ

```text
Claude / Codex / Kiro
        │
        │ workspace hook / skill
        ▼
.taviq/runtime.json
  tool / mode / model(optional)
        │
        │ prepare-commit-msg
        ▼
Git commit
  Taviq-Provenance: v1
  Taviq-Tool: claude
  Taviq-Mode: agent
  Taviq-Model: <取得できた場合のみ>
        │
        ▼
GitHub
        │
        ▼
GitHub Actions
        │
        ▼
PR Provenance Summary

Coverage 80%
Confirmed 4 / 5 commits
Unknown 1 commit
Tools: Claude, Codex
```

Taviqは、証拠がないcommitを「人間だけで作った」とは判定しません。**UnknownはUnknownのまま扱います。**

### 導入

リポジトリで次を実行します。

```bash
python3 scripts/install_basic.py
```

これによりrepository-localの `prepare-commit-msg` hookが設定されます。

その後は通常どおりClaude / Codex / Kiroで開発してcommitします。対応workspace integrationがAI tool情報を一時的な `.taviq/runtime.json` へ記録し、Git hookが最小限のcommit trailerへ変換します。

`.taviq/runtime.json` はGit管理対象外です。

### 対応

| Tool | Basic integration |
| --- | --- |
| Claude Code | workspace SessionStart hook |
| Codex | workspace/plugin SessionStart hook + Skill fallback |
| Kiro | workspace Agent Spawn hook |

ModelはBasicの必須項目ではありません。公式に確実に取得できる場合だけ記録し、推測しません。

### Gitに残すもの

```text
Taviq-Provenance: v1
Taviq-Tool: claude
Taviq-Mode: agent
Taviq-Model: <optional>
```

### Gitに残さないもの

- Prompt / AI Response
- ソースコード本文 / Diff本文
- Token / Credit
- AI利用コスト
- Chat履歴
- 人の作業時間
- 個人の生産性スコアやランキング

Basicは「AI関与の来歴」を記録する機能です。来歴だけから「AIで生産性が上がった」「ROIが高い」「品質が改善した」とは判断しません。

### BasicとAdvanced

**Basic（標準）**

`Skill / Hook → Git trailer → GitHub Actions`

サーバー不要。AI関与の明示的な来歴とcoverageを扱います。

**Advanced（任意・Basic完成まで開発凍結）**

Local/Cloud Collector、usage、cost、Self-hosted/Cloud transport等を追加し、AI Engineering Economicsなどの高度な判断材料を扱います。

BasicだけでAdvancedを要求しません。

### 詳細仕様

- [Basic setup](docs/basic.md)
- [Data Capability Model](docs/data-capability-model.md)
- [AI Provenance & Storage Architecture](docs/ai-provenance-storage.md)
- [Deployment Modes](docs/deployment-modes.md)
- [Implementation Roadmap](docs/ROADMAP.md)

## Quick start

Export pull requests with GitHub CLI:

```bash
gh pr list --repo owner/repository --state all --limit 1000 \
  --json createdAt,mergedAt,additions,deletions,reviews \
  > /tmp/prs.json
```

Generate a report:

```bash
python3 taviq.py \
  --input /tmp/prs.json --repo owner/repository \
  --since 2026-08-01 --until 2026-09-01 \
  --format html --output /tmp/taviq-report.html
```

For multiple repositories, repeat `--input` and `--repo`. Add `--ai-input samples/ai-roi-input.json` to include the AI investment section.

## Samples

- `samples/engineering-delivery-review.md`
- `samples/generative-ai-investment-review.md`

Sample report numbers are synthetic and exist only to demonstrate the deliverable.

## Method

Metric definitions and interpretation principles are developed separately in `kpi-playbook`. Taviq is the product implementation: data in, engineering intelligence out.
