# Taviq Roadmap — Provenance First

## Product focus

Taviq = **AI Engineering Provenance Layer**.

優先順位は「AI価値を分析すること」ではなく、分析・監査・ガバナンスに使えるAI関与の証拠を、低負荷・privacy-consciousに作ること。

## v0.1 — Basic provenance

- [x] Serverless architecture
- [x] Minimal commit trailer
- [x] GitHub Actions PR summary
- [x] Claude workspace hook
- [x] Codex workspace/plugin hook + Skill fallback (superseded by machine-level hook)
- [x] Kiro workspace hook (removed; machine-level wiring pending)
- [x] Unknown != human-only
- [x] Model optional / never guessed
- [x] Prompt / source / token / costをGitへ保存しない
- [x] Zero-AI-overhead benchmark / CI guard
- [x] 実Claude Codeでhook発火をdogfood
- [ ] 実Codexでhook発火をdogfood
- [ ] 実Kiroでhook発火をdogfood
- [ ] 実PRでend-to-end確認
- [x] reversible install / uninstall UX
- [ ] Basic v0.1 release

## v0.2 — Organization-ready provenance

- [x] global Taviq CLI: install once per developer machine
- [x] `taviq init / deinit / doctor` repository UX
- [ ] organization policy schema
- [ ] repository opt-in / policy discovery
- [ ] GitHub reusable workflow for centralized PR aggregation
- [ ] organization rollout without copying Taviq implementation into every repository
- [ ] organization privacy / governance defaults
- [ ] repository / PR / commit level reporting boundaries
- [ ] organization policy compatibility / version handling

## v0.2.x — Provenance quality

- [ ] provenance schema versioning
- [x] commit trailer validation (`taviq validate`)
- [ ] tool / mode taxonomyを安定化
- [ ] provenance coverage semanticsを固定
- [x] provenance spoofing / trust model
- [x] BasicはZero-secret / Recorded-or-Unknownに固定
- [x] 独自HMAC/signing systemを採用しない
- [ ] 標準的なsupply-chain attestation/signing方式を必要性から評価
- [x] spoofing / tampering threat model
- [ ] monorepo / worktree / squash merge対応
- [ ] merge commit / rebase対応
- [ ] bot / cloud agent provenance
- [ ] Web / Mobile → Cloud Agent provenance

## v0.3 — Zero-touch organization adoption

- [ ] GitHub App / Ruleset based rollout evaluation
- [ ] organization-wide enable / disable controls
- [ ] centralized policy distribution
- [ ] fleet-wide `doctor` / adoption visibility without developer productivity scoring
- [ ] reusable workflow / App upgrade strategy
- [ ] GitLab / other Git forge distribution model

## Adoption follow-ups

- [ ] one-command install
- [ ] organization-wide rollout
- [ ] GitHub reusable workflow / App検討
- [ ] policy configuration
- [ ] privacy / governance onboarding
- [ ] provenance export format
- [ ] audit-friendly report

## Future integrations

- [ ] additional AI coding tools
- [ ] IDE integrations
- [ ] CI/CD attestation
- [ ] external provenance standards / attestationsとの互換性検討

## Out of core scope

以下はTaviq Provenanceの中心責務にしない。

- Engineering KPI dashboard
- Executive KPI narrative
- AI ROI calculator
- developer productivity scoring
- individual ranking
- causal productivity claims

必要ならprovenance exportを通じて別分析レイヤーへ提供する。

KPI設計・Delivery/Quality/ROIの読み方はKPI Playbook側の責務として扱う。

## Definition of Done

通常のAI開発フローを変えずに、追加AI call/token/creditなしで、どのcommit/PRにどのAI tool/modeの関与が確認できたかを記録できる。

記録できないものはUnknownとして残り、Taviqが推測で埋めない。


## Target architecture migration checklist

### Phase A — Single binary Core
- [x] Go Core selected
- [x] binary-only init / hook / doctor / deinit acceptance
- [x] cross-build macOS/Linux/Windows
- [x] Python removed from Core runtime
- [x] stable release artifact/version command
- [x] SHA-256 checksums for binary releases
- [ ] binary signing strategy

### Phase B — Machine-level install
- [x] define `taviq install / uninstall` machine lifecycle
- [x] machine config location
- [ ] machine config schema
- [x] reversible global Git integration
- [x] preserve existing global Git configuration
- [ ] upgrade path for installed binary/config
- [ ] Homebrew distribution
- [ ] Windows installation path
- [ ] Linux installation path

### Phase C — Repository implementation zero
- [x] define minimal `.taviq.yml` marker schema
- [x] make `taviq init` marker-only
- [x] make `taviq deinit` marker-only
- [x] global Git integration ignores non-enabled repositories
- [x] remove repository-local hook files
- [x] doctor validates marker + machine integration

### Phase D — Machine-level AI integrations
- [x] Claude machine-owned adapter (`taviq-claude`)
- [x] Claude tool configuration wiring
- [x] Codex machine-owned adapter (`taviq-codex`)
- [x] Codex tool configuration wiring
- [x] Kiro machine-owned adapter (`taviq-kiro`)
- [ ] Kiro tool configuration wiring (blocked: hook trigger names inconsistent across Kiro docs)
- [x] integrations call `taviq observe`
- [x] preserve existing user tool configuration
- [x] safe uninstall of only Taviq-owned configuration

### Phase E — Organization policy
- [ ] organization policy schema
- [ ] trusted policy discovery
- [ ] org policy can enable repository without marker
- [ ] local marker / org policy precedence rules
- [ ] policy version compatibility
- [ ] organization privacy defaults
- [ ] fleet doctor/status without productivity scoring

### Phase F — Optional forge integrations
- [ ] reusable GitHub workflow
- [ ] GitHub App feasibility
- [ ] Ruleset / Quality Gate rollout guide
- [ ] GitLab integration model
- [ ] Bitbucket integration model
- [ ] Core remains functional with none of these installed

### Phase G — Zero-touch acceptance
- [ ] fresh managed machine receives Taviq automatically
- [ ] developer clones org repository
- [ ] supported AI tool automatically records observation
- [ ] normal commit receives v1 provenance
- [ ] developer performs no Taviq-specific setup
- [ ] unrelated/non-enabled repositories remain untouched
- [ ] central uninstall/upgrade is safe and reversible
