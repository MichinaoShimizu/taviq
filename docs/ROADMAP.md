# Taviq Implementation Roadmap

完了条件を確認できた項目だけチェックする。

## Phase 0 — Decision foundation
- [x] Data Capability Model
- [x] KPI / KGI / CSF / counter metric / referenceを分離
- [x] Evidence Level
- [x] AI ROIの時間価値・現金効果・感度分析を分離
- [x] Execution-centric provenance architecture
- [x] Portable Taviq Provenance Skill

## Phase 1 — Local provenance MVP
- [x] Local Event Store
- [x] allow-list方式でPrompt / Response / code / diffを非保存
- [x] repository / worktree / branch / HEAD correlation
- [x] Claude hook adapter MVP
- [x] 明示file pathをsessionへ記録
- [x] session単位のfile / commit correlation
- [x] provenance coverage集約
- [x] Unknown != human-onlyのテスト
- [ ] 実Claude Code環境でdogfood
- [ ] session lifecycle実データ検証
- [ ] raw event TTL / cleanup

## Basic MVP — Definition of Done\n- [x] Server不要\n- [x] repo-local Git hook installer\n- [x] tool / mode / modelの最小commit trailer\n- [x] Unknown時はtrailerを書かない\n- [x] trailer付与のidempotency\n- [x] PRでGitHub Actions Summary\n- [x] Prompt / code / usage / costをGitへ保存しない\n- [x] Claude Code workspace hookでtool/modeを自動設定\n- [ ] Claude modelを公式に取得できる場合のみ自動設定\n- [x] Codex workspace Skillでtool/modeを設定\n- [ ] Codex lifecycle hookでSkill依存をなくす\n- [ ] Codex modelを公式に取得できる場合のみ自動設定\n- [x] Kiro workspace hookでtool/modeを自動設定\n- [ ] Kiro modelを公式に取得できる場合のみ自動設定\n- [ ] 実PRでend-to-end dogfood\n\n## Phase 2 — GitHub integration\n- [x] Basic mode: Skill → minimal commit trailer → GitHub Actions
- [x] GitHub Check用summary生成
- [x] PR changed-files入力からcoverage report JSON生成
- [x] MVPはread-only GitHub Actions + Job Summary。Check Run書込は後続で決定
- [x] Basic modeをGitHub Actions Job Summaryへ表示\n- [ ] Check Runとして独立表示（任意の次段階）
- [x] privacy-minimal provenance envelopeを定義\n- [x] replaceable envelope transport契約を定義\n- [x] short-lived GitHub Actions artifact workflowを追加\n- [x] Local producer outboxを実装\n- [x] Collectorとtransportを分離\n- [x] GitHub artifact direct-upload案を棄却（外部upload APIなし / workflow dispatchはActions writeが必要）\n- [x] Local/Self-hosted relay ingestion API MVP\n- [x] Self-hosted relay outbox transport MVP\n- [ ] TLS / org scoping / rate limit / durable DB\n- [ ] Taviq Cloud HTTPS transport\n- [ ] commit/session evidenceをPRへ集約
- [ ] tool / mode / model / coverage表示
- [ ] low coverage時にEvidenceが弱いと表示
- [x] GitHub書込権限をLocal Collectorから分離

## Advanced — Frozen until Basic v0.1 is complete\n\nDo not add Advanced Collector/Relay/Economics features until all unchecked items in Basic MVP Definition of Done are complete.\n\n## Phase 3 — Tool adapters
### Claude
- [ ] 公式hook eventごとのフィールド検証
- [ ] model/version
- [ ] token/cache usage
- [ ] Cloud/Web/Mobile execution
### Codex
- [ ] Codex CLI adapter
- [ ] Codex Cloud adapter
- [ ] Agent Skill連携
- [ ] model/version/usage
- [ ] Mobile/Web → Cloud correlation
### Kiro
- [ ] Kiro CLI hooks
- [ ] Kiro IDE
- [ ] Kiro Crew / multi-agent
- [ ] Agent Skills連携
- [ ] model/version/credit/usage
- [ ] Web/Mobile correlation

## Phase 4 — AI Engineering Economics
- [ ] Tool / Model / Mode / Task type集計
- [ ] 品質合格条件
- [ ] Human oversight / rework
- [ ] AI成功案件あたり総費用
- [ ] 正味削減時間
- [ ] Capacity Value
- [ ] actual / estimated cost分離
- [ ] 損益分岐
- [ ] ROI sensitivity
- [ ] AI利用量だけからROIを推測しないguardrail

## Phase 5 — Quality
- [ ] CI
- [ ] deploy
- [ ] change failure / rollback
- [ ] incident
- [ ] SLO / error budget
- [ ] 品質未接続時は投資拡大を断定しない

## Phase 6 — Work flow
- [ ] GitHub Issues
- [ ] Jira / Linear等のtask source
- [ ] 着手→品質合格→提供
- [ ] WIP / wait / rework
- [ ] Task type / 難易度等の比較条件

## Phase 7 — Product / Business
- [ ] Product Analytics contract
- [ ] feature adoption / customer outcome
- [ ] CRM / Finance contract
- [ ] revenue / gross margin / retention / actual cost
- [ ] Engineering → Product → Businessは仮説として表示
- [ ] 検証条件なしの因果表現を禁止

## Phase 8 — Productization
- [ ] Data connection / Capability UI
- [ ] 言える / 言えない / 必要データ UI
- [ ] Executive narrative
- [ ] KPI management UI
- [ ] AI investment decision UI
- [ ] Local-only / Self-hosted / Cloud
- [ ] retention / deletion / export
- [ ] RBAC
- [ ] privacy / governance onboarding

## Phase 9 — Validation / business
- [ ] Taviq自身で継続dogfooding
- [ ] 実チーム相当のend-to-end case study
- [ ] CTO / VPoE / EMインタビュー
- [ ] 経営会議で答えられなかった問いを3件以上収集
- [ ] Taviqで回答可能か検証
- [ ] 有料PoC
- [ ] 月5万円売上の最初の顧客仮説を検証

## MVP Definition of Done
通常のAI開発だけでprovenanceが透過的に記録され、GitHub変更と結び付き、接続データの範囲内で「何が言える / 言えない / 次に何が必要」を正確に説明できること。