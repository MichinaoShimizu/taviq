# TAVIQ

**Engineering Intelligence**

Delivery · Quality · AI · ROI

Taviq turns engineering delivery signals into decision-ready reports for engineering leaders and executives.

## Report hierarchy

Taviq separates the report by decision level:

1. **Executives** — investment, released capacity, delivery outcome, quality guardrails, business connection, and the decision/question requiring attention.
2. **Engineering leaders / EMs** — delivery-system signals such as cycle time, review latency, AI ROI, and AI/non-AI observational comparisons.
3. **Diagnostic detail** — repository-level PR throughput, size, cycle, and review metrics used to investigate why the upper-level signal moved.

PR counts and review latency are diagnostic inputs; they are not presented as the primary executive outcome.

The intended value chain is:

`Engineering investment → capacity → delivery → quality → business outcome`

AI reporting follows the same chain. Adoption, generated-code share, or token usage are not treated as business outcomes.

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
