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
