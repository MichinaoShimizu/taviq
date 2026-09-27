# Taviq Roadmap — Provenance First

## Product focus

Taviq = **AI Engineering Provenance Layer**.

優先順位は「AI価値を分析すること」ではなく、分析・監査・ガバナンスに使えるAI関与の証拠を、低負荷・privacy-consciousに作ること。

## v0.1 — Basic provenance

- [x] Serverless architecture
- [x] Minimal commit trailer
- [x] GitHub Actions PR summary
- [x] Claude workspace hook
- [x] Codex workspace/plugin hook + Skill fallback
- [x] Kiro workspace hook
- [x] Unknown != human-only
- [x] Model optional / never guessed
- [x] Prompt / source / token / costをGitへ保存しない
- [x] Zero-AI-overhead benchmark / CI guard
- [ ] 実Claude Codeでhook発火をdogfood
- [ ] 実Codexでhook発火をdogfood
- [ ] 実Kiroでhook発火をdogfood
- [ ] 実PRでend-to-end確認
- [x] reversible install / uninstall UX
- [ ] Basic v0.1 release

## v0.2 — Provenance quality

- [ ] provenance schema versioning
- [ ] commit trailer validation
- [ ] tool / mode taxonomyを安定化
- [ ] provenance coverage semanticsを固定
- [x] provenance spoofing / trust model\n- [x] BasicはZero-secret / Recorded-or-Unknownに固定\n- [x] 独自HMAC/signing systemを採用しない\n- [ ] 標準的なsupply-chain attestation/signing方式を必要性から評価
- [x] spoofing / tampering threat model
- [ ] monorepo / worktree / squash merge対応
- [ ] merge commit / rebase対応
- [ ] bot / cloud agent provenance
- [ ] Web / Mobile → Cloud Agent provenance

## v0.3 — Adoption

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
