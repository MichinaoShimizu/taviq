# Taviq AI Provenance & Storage Architecture

## 目的

Taviqは、Kiro・Claude・CodexなどのAI開発ツールの利用を、開発者の日常操作を増やさずに仕事・変更単位へ結び付ける。

収集の目的は「誰がAIを多く使ったか」を監視することではない。**どのAI executionが、どの仕事・変更へ関与したか、その証拠の強さ、利用量、モデル、費用を、品質・人の負荷・成果と後から接続できる形で残すこと**である。

## 基本原則

1. **Execution-centric** — 端末ではなくAIの実行sessionを追う。
2. **Local-first** — local executionの生イベントは原則ローカルで受け取る。
3. **日常操作を増やさない** — 導入後はhook / adapter / integrationで自動収集する。
4. **秘密に収集しない** — 目的、項目、保存場所、閲覧範囲、保持期間を事前に示す。
5. **内容ではなくprovenanceを取る** — Prompt、Response、コード本文はデフォルト非収集。
6. **unknownを許す** — 取得不能値を推測しない。証拠なしをAI不使用としない。
7. **Gitには最小限** — token、費用、個人情報、詳細sessionを永続履歴へ埋め込まない。
8. **個人評価に使わない** — 個人別AIランキング、生産性スコアを製品機能にしない。
9. **実測・推計・換算を分ける** — vendor usage、推計cost、時間価値、実請求を別に扱う。

## 初期対象

- **Kiro** — CLI、Crew / multi-agent、取得可能なその他surface
- **Claude** — Claude Codeを中心とする開発利用
- **Codex** — Codex CLI / Cloud等の取得可能な開発利用

ツール固有イベントはadapterで共通eventへ正規化する。存在しないフィールドをTaviqが補完しない。

## DeviceではなくExecutionを追う

PC、Web、Mobileは操作面であり、変更処理は別の環境で実行されることがある。

```text
PC / Mobile / Web
       │ instruction
       ▼
Kiro / Claude / Codex
       │
       ▼
Local / Cloud / GitHub execution
       │
       ▼
repository / task / commit / PR
       │
       ▼
Taviq provenance
```

共通eventでは操作面と実行環境を分離する。

```yaml
interaction:
  surface: cli | ide | web | mobile | github

execution:
  environment: local | cloud | github | remote
  session_id: ...
```

例: スマホからCodex Cloud Agentへ指示した場合。

```yaml
ai:
  tool: codex
interaction:
  surface: mobile
execution:
  environment: cloud
```

スマホへのLocal Collector導入を前提にしない。Cloud/Agent側の公式event、API、GitHub上の結果等からexecution provenanceを取得する。

同じ仕事をPC、Web、Mobileで継続しても、repository / task / session / commit / PRの識別子で統合する。

### 主な収集ポイント

| 開発形態 | 収集ポイント |
| --- | --- |
| PC CLI | Local Collector + tool adapter |
| IDE | IDE/tool event + Local Collector |
| Web → Cloud Agent | Cloud/Agent integration |
| Mobile → Cloud Agent | Cloud/Agent integration |
| GitHub上のAgent | GitHub/Agent integration |
| Remote dev environment | 実行環境側Collector / integration |

## 保存アーキテクチャ

```text
Kiro / Claude / Codex
        │
        ▼
1. Local / Execution Event Store
        │ correlate
        ▼
2. Git Provenance
   minimal reference only
        │ aggregate
        ▼
3. Analytics Store
   Local / Self-hosted / Taviq Cloud
```

### 1. Local / Execution Event Store

local executionの例:

```text
~/.taviq/
  events/
  state/
  config/
```

用途:

- sessionとrepository/worktreeを結ぶ
- file変更とcommit対象を照合
- model / usage / modeをcommit/PRへ集約
- 永続化前に不要データを除去

Cloud executionでは同等の処理をintegration側で行い、スマホ等へraw eventを保存しない。

### 2. Git Provenance

Gitは長期間残るため分析データ本体を保存しない。

必要ならcommitへ最小参照のみ残す。

```text
Taviq-Provenance: v1:8fd31...
```

Gitへ原則保存しない:

- token / credit詳細
- 金額
- Prompt / Response
- コード / diff本文
- 個人別利用情報
- 詳細session履歴

PRではGitHub Check等でcoverageと状態を表示する。PR本文を分析DBにしない。

### 3. Analytics Store

正規化済みの必要最小限データを保存する。

**Local-only** — 顧客環境から出さない。PoC・小規模・高セキュリティ環境向け。

**Self-hosted** — 顧客管理のDBへ保存。組織横断分析や社内データ基盤接続向け。

**Taviq Cloud** — 明示的に有効化した組織のみ送信。Cloud利用をprovenance収集の必須条件にしない。

## 共通AI Provenance Event

```yaml
schema_version: 1

event:
  id:
  occurred_at:

context:
  organization:
  repository:
  worktree:
  branch:
  task_id:
  commit_sha:
  pr_number:

ai:
  provider:
  tool:            # kiro / claude / codex
  mode:            # assist / generate / agent / crew / mixed
  model:
    name:
    version:

interaction:
  surface:         # cli / ide / web / mobile / github

execution:
  environment:     # local / cloud / github / remote
  session_id:

usage:
  input_tokens:
  output_tokens:
  cache_read_tokens:
  cache_write_tokens:
  requests:
  credits:
  usage_unit:

cost:
  actual:
  estimated:
  currency:
  source:

change:
  files_touched:

provenance:
  source:          # agent_event / ide_event / vendor_api / commit_trailer / self_reported
  confidence:      # confirmed / partial / unknown
```

取得できたフィールドだけ記録する。

## AI involvement

```text
none       AI不使用を明示的に確認
assist     補完・相談
generate   AIによる成果物生成
agent      Agentへタスク委任
crew       複数Agentによる協調実行
mixed      複数mode
unknown    判断不能
```

**証拠がないことを none としない。**

## Commit / PRへの集約

3ファイル中2ファイルでAI関与を確認し、1ファイルは証拠なしなら:

```text
confirmed AI files   2
unknown files        1
provenance coverage  66.7%
mode                 agent
tool                 claude
```

これは「AIがコードの66.7%を書いた」という意味ではない。**provenanceを確認できた変更範囲が66.7%**という意味。

PRでは複数commitを集約して、coverage、confirmed / partial / unknown、tool、mode、取得可能ならmodelを表示する。

## Model / Version / Token / Credit / Cost

### Model

provider / model name / version or identifierを取得できる場合に記録する。推測しない。

### Usage

ツール固有単位を保持する。

- input / output token
- cached token
- request
- credit
- compute time
- included usage
- overage

共通化できない単位を無理にtokenへ変換しない。

### Cost

優先順位:

1. 請求/usage API由来のactual
2. usage × 合意単価によるestimated
3. unknown

actualとestimatedを混ぜない。

## デフォルトで収集しないもの

- Prompt本文
- AI Response本文
- ソースコード本文
- Diff本文
- チャット履歴
- 個人別AI利用ランキング
- 個人別生産性スコア

file pathもポリシーに応じてhash化/非送信を選択可能にする。

## 保持

### Raw event

commit/PRとの照合が目的で、永久保存しない。

- 未集約: 短期保持
- 集約済み: configurable TTL後に削除
- 送信済み: 確認後TTLで削除

既定TTLは実装前にセキュリティ・運用要件を確認して決める。

### Analytics data

比較期間・監査要件に合わせて設定可能。rawより長期保持可能だが、必要最小限の正規化データのみ残す。

## Privacy / Governance

導入時に明示する:

- 取得目的
- 取得項目 / 非取得項目
- 保存場所
- 閲覧可能な役割
- 保持期間
- 削除方法
- 個人評価に使わないこと
- 外部Cloud送信の有無

人の作業時間サンプリングはprovenanceとは別カテゴリとして、人事・法務・労務上の確認を行う。

## API境界

提供する方向:

```text
/teams/{team}/ai-metrics
/workflows/{workflow}/ai-economics
/models/{model}/quality-cost
```

提供しない方向:

```text
/users/{user}/productivity-score
/users/{user}/ai-ranking
```

## Provenanceから価値まで

Provenance単体で生産性を判断しない。

```text
AI provenance
      +
Human effort
      +
Work completion
      +
Quality
      +
AI cost
      +
Product / Business outcome
```

Provenanceは「AI関与の証拠」であり、「AIが価値を生んだ証拠」ではない。

## 初期実装順

1. 共通event schema
2. Local Event Store
3. repository / worktree / task / commit correlation
4. Claude adapter
5. Codex adapter
6. Kiro CLI adapter
7. Kiro Crew adapter
8. Cloud / GitHub execution integration
9. GitHub Checkでprovenance coverage表示
10. Local analytics
11. Self-hosted / Cloud transport

実際のadapter順は各ツールの公式hook/event/usage取得能力の調査結果で変更する。

## プロダクト原則

Taviqは「誰がAIを多く使ったか」を測る製品ではない。

**どの種類の仕事で、どのAI・モデル・使い方が、品質と人の負荷を守りながら価値を生んだかを判断できる証拠を作る。**

その証拠を得るために、開発者へ余計な日常操作を要求しない。
