# Engineering Delivery Review — SAMPLE

> **Demo report.** The numbers below are synthetic and are provided only to show the deliverable format. They are not measurements of a real company or individual.

**Period:** 2026-08-01 – 2026-09-01  
**Comparison:** preceding equal-length period  
**Scope:** 3 repositories / delivery-system level only

## Executive summary

Delivery volume remained broadly stable while the median merge cycle time increased from **25.1h to 34.8h (+38.6%)**. The strongest accompanying signal is first-review wait, which increased from **5.8h to 9.4h (+62.1%)**. This does not establish causality, but it makes review latency the first place to investigate.

PR size also increased from **148 to 196 changed lines (+32.4%)**. A useful next step is to separate cycle time by PR-size band and repository before changing process policy.

## KPI snapshot

| Metric | Current | Previous | Change |
| --- | ---: | ---: | ---: |
| PRs opened | 184 | 177 | +4.0% |
| Merged PRs | 169 | 164 | +3.0% |
| Median merge cycle | 34.8h | 25.1h | +38.6% |
| Median first review | 9.4h | 5.8h | +62.1% |
| Median PR size | 196 lines | 148 lines | +32.4% |
| Reviewed PRs waiting >24h | 21.7% | 12.9% | +68.2% |

## Repository breakdown

| Repository | PRs | Merge cycle | First review | PR size |
| --- | ---: | ---: | ---: | ---: |
| api | 73 | 29.2h | 7.1h | 182 |
| web | 81 | 41.5h | 12.8h | 221 |
| platform | 30 | 31.0h | 6.4h | 155 |

## What to investigate next

1. **Review latency in web** — break down first-review wait by weekday and PR-size band. Check queueing and reviewer availability before changing targets.
2. **Larger PRs** — compare cycle time across size bands. If the relationship persists, inspect why work is batching into larger changes.
3. **Long-wait tail** — inspect the distribution behind the 21.7% of reviewed PRs waiting over 24 hours rather than relying on the median alone.

## Recommended experiment

For four weeks, visualize PRs over 300 changed lines at planning/review time and encourage splitting where it does not increase coordination cost. Track median and 75th-percentile first-review wait and merge cycle alongside throughput. Do not use the metric as an individual target.

## Interpretation guardrails

- These metrics describe the delivery system, not developer performance.
- Period-over-period changes are signals for investigation, not proof of a cause.
- Repository mix, release cycles, incidents, staffing changes, holidays, and work type can change the numbers.
- Decisions should combine quantitative signals with team context and qualitative evidence.

## What a customer receives

A monthly engagement can use the same structure with the customer's GitHub data: an executive summary, KPI snapshot, repository/team-level breakdowns where appropriate, investigation priorities, and one or two measurable experiments for the next period.
