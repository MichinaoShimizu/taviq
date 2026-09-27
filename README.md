# TAVIQ

**Engineering Intelligence**

Delivery · Quality · AI · ROI

Taviq turns engineering delivery signals into decision-ready reports for engineering leaders and executives.

## What it measures

- Delivery: PR throughput, merge cycle time, first-review wait, PR size, long review waits
- Generative AI: net human time saved, capacity value, program cost, estimated ROI
- AI delivery comparison: AI-involved vs non-AI changes with provenance coverage
- Guardrails: metrics describe the delivery system, not individual performance; observational comparisons are not causal estimates

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
