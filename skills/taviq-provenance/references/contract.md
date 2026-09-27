# Taviq Skill Contract

The portable skill is an instruction layer, not the authoritative event collector.

## Responsibilities

### Skill
- preserves privacy and measurement rules
- invokes deterministic Taviq recording commands when available
- avoids fabricated provenance
- keeps claims within the Data Capability Model

### Collector / adapter
- captures deterministic tool events
- obtains model / usage / credit / cost when officially exposed
- correlates execution with Git
- stores raw events with TTL
- creates minimal provenance references

### Analytics
- aggregates commit/PR provenance
- calculates provenance coverage
- joins quality, human effort, cost, product and business sources
- assigns evidence level

## Confidence

- confirmed: deterministic tool/vendor/collector evidence supports the record.
- partial: only part of the relevant change/execution has reliable evidence.
- unknown: evidence is insufficient.

Absence of a Taviq event is never proof of AI non-use.