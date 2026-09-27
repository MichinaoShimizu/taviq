# Taviq Development Skill

Use this skill before changing Taviq.

## Read first

1. `README.md`
2. `docs/provenance-schema.md`
3. `docs/verified-provenance.md`
4. `docs/adr/README.md`
5. `docs/ROADMAP.md`

## Non-negotiable Basic rules

- Taviq is provenance-first.
- Basic is zero-server, zero-secret and zero-extra-AI-call.
- Use Recorded / Unknown. Unknown is not Human-only.
- Recorded is not Verified or vendor-attested.
- Tool/model/mode sets represent observed presence, not contribution percentages.
- Never guess model/tool metadata.
- Do not store prompt, response, source/diff, token/credit, cost, chat history, developer identity or productivity scores in Basic provenance.
- Do not silently change v1 field semantics.
- Prefer standard-library deterministic code for the Basic recording path.
- Preserve existing Git configuration on install/uninstall.

## Before opening or merging a PR

Run:

```bash
python3 scripts/lint_contract.py
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/benchmark_basic.py
```

Review the change as three roles:

### Semantics reviewer

Ask what each new field/result actually proves and what it does not prove. Reject percentage/causal/authorship interpretations not supported by the schema.

### Security/privacy reviewer

Look for new secrets, network calls, permissions, durable sensitive data, identity tracking and misleading verification claims.

### Release reviewer

Check README/docs links, schema compatibility, install/uninstall behavior, CI, overhead budget and roadmap consistency.


## Repository editing safety

- Do not modify GitHub Actions YAML by escaped-newline string insertion/replacement.
- When structurally changing a workflow, rewrite the relevant YAML block/file with real newlines and let Contract Lint validate it.


## Documentation synchronization

Implementation changes are not complete until user-facing documentation matches the resulting behavior.

Before merging an implementation PR:

- update README when install, commands, supported tools, repository state, or user workflow changes
- update the relevant design/operation document when architecture or lifecycle changes
- do not defer obvious documentation drift to a follow-up PR
- keep README concise; move detailed rationale to docs
