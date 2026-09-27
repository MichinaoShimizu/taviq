# Taviq Deployment Modes

## Basic — default

The default Taviq path should work without a Taviq server.

```text
Kiro / Claude / Codex
        ↓
Taviq Skill
        ↓
minimal Git commit trailer
        ↓
GitHub
        ↓
GitHub Actions
        ↓
PR provenance summary
```

### Allowed commit metadata

Only low-sensitivity, durable provenance metadata:

```text
Taviq-Provenance: v1
Taviq-Tool: claude
Taviq-Mode: agent
Taviq-Model: <model-id-if-exposed>
```

Model is optional. Unknown values are omitted, not guessed.

Never store in Git:

- prompt / response
- source / diff
- token / credit counts
- cost
- session event history
- developer productivity scores
- human-effort measurements

### What Basic can answer

- which commits have explicit AI provenance
- observed tool / mode / model when recorded
- commit-level provenance coverage
- PR-level mix of confirmed AI provenance and unknown commits
- comparison inputs for later delivery/quality analysis

Basic cannot calculate reliable AI ROI, net time saved, actual AI cost or human oversight from trailers alone.

## Advanced — optional

Use Collector / Outbox / Relay only when richer economics or execution evidence is required.

```text
AI execution
   ↓
Local / Cloud Collector
   ↓
usage / model / execution metadata
   ↓
Outbox / Self-hosted or Cloud transport
   ↓
Taviq analytics
```

Advanced enables inputs such as token/credit usage, actual/estimated cost, richer session evidence and later human-effort joins.

The Advanced path must never be required merely to display Basic provenance in GitHub.

## Product rule

Start with Basic. Ask for Advanced data only when the organization wants a decision that Basic cannot support.
