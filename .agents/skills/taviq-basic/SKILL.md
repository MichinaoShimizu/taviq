---
name: taviq-basic
description: Mark Codex engineering work with minimal Taviq Basic provenance so Git commits can be summarized by GitHub Actions without a Taviq server.
---

# Taviq Basic for Codex

At the beginning of engineering work in this repository, run:

```bash
python3 scripts/set_runtime.py --tool codex --mode agent --cwd "$PWD"
```

Do not add prompt, response, token, cost, source-code, or diff data. Do not invent model identifiers. The repository Git hook will add the minimal Taviq trailer when a commit is created.
