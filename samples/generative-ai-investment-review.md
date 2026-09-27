# Generative AI Investment Review — SAMPLE

> Demo only. All numbers are synthetic. This illustrates the reporting model; it is not evidence about a real company, tool, team, or individual.

## Investment view

| Value / cost | Current period |
| --- | ---: |
| Net human time saved | 72.0h |
| Estimated capacity value | ¥468,000 |
| AI program cost | ¥140,000 |
| Estimated net benefit | ¥328,000 |
| Estimated ROI | 234.3% |

**Interpretation:** the ROI above values released capacity at loaded hourly cost. It is not booked cash profit. Time saved includes prompting, checking and rework and should be estimated against comparable work.

## Adoption and execution

| Signal | Value |
| --- | ---: |
| Sustained AI adoption | 68.0% |
| Agent task success | 61.0% |
| AI provenance coverage | 91.4% |
| Provenance unrecorded | 16 changes |

Adoption is a rollout signal, not a productivity outcome. Agent success requires the agreed quality and intervention conditions, not merely code generation or test execution.

## Delivery comparison

| Condition | PRs | Median merge cycle | Median first review | Median PR size |
| --- | ---: | ---: | ---: | ---: |
| AI involved | 96 | 29.4h | 8.7h | 214 lines |
| No AI recorded | 72 | 35.8h | 7.9h | 171 lines |

The AI-involved group shows a lower merge-cycle median in this demo, but it also contains larger changes and a different review profile. This is an **observational comparison**, not a causal estimate. Work mix, difficulty, repository, familiarity and rollout timing must be controlled before attributing the difference to AI.

## Quality and verification guardrails

A paid review should pair the value estimate with quality signals such as change failure rate, escaped defects, verification/rework time, abandoned agent changes, and human-review coverage. A faster cycle with worse quality is not counted as an AI productivity win.

## Management questions for the next period

1. Is net time saved still positive after prompting, review, correction and agent supervision?
2. Where did the released capacity go: more delivery, quality work, customer work, learning, or simply unobserved slack?
3. Do matched categories of work show the same direction as the aggregate AI/non-AI comparison?
4. Did quality, reliability or security guardrails worsen while delivery speed improved?
5. Is provenance coverage high enough to make the AI/non-AI comparison usable?

## Decision framing

Continue, expand, constrain or redesign AI use based on the combination of value, cost, delivery outcomes and quality guardrails. Do not optimize adoption rate, generated-code share, token usage, or suggestion acceptance as standalone business outcomes.
