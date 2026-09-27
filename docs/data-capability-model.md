> **Historical / experimental.** This document describes an earlier Collector/Analytics design and is not the current Taviq Basic architecture. Current Basic is zero-server and records minimal provenance through Git trailers and GitHub Actions. See [README](../README.md), [Basic](basic.md), and [Roadmap](ROADMAP.md).

# Taviq Data Capability Model

## 目的

Taviqは、接続されたデータから「実際に観測できること」と「推測にすぎないこと」を混同しない。

この文書は、各データソース単体で分かること、複数ソースを組み合わせて初めて分かること、追加の検証なしには因果として言えないことを定義する。Taviqのコネクタ、分析ロジック、UI、経営向け文章生成はこの境界に従う。

## 基本原則

1. **観測できない値を補完しない。** 未接続のデータは `未接続` と表示する。
2. **利用・活動・成果・価値を分ける。** AI利用率は生産性でもROIでも事業成果でもない。
3. **時間価値と現金効果を分ける。** 削減時間 × 単価はキャパシティ価値の換算であり、現金利益ではない。
4. **関連と因果を分ける。** AI関与変更のCycle Timeが短くても、それだけでAIによる改善とは言わない。
5. **KPIの役割を混ぜない。** 重点KPI、カウンターメトリクス、参照値、KGIを区別する。ROI試算は原則として投資判断の参照値。
6. **測定条件を表示する。** 対象、期間、母数、確定時点、実測/推計、比較条件を可能な限り残す。
7. **個人評価に使わない。** 開発システムと投資判断の改善を目的とする。

## 1. データソース単体の能力

| データソース | 単体で観測・計算できる主なもの | 単体で提供できる価値 | 単体では言えないこと |
| --- | --- | --- | --- |
| GitHub | PR数、PRサイズ、PR作成→Merge時間、初回Review待ち、Review状況、滞留PR、Revert等 | コード変更フローの速度・滞留・変更サイズの把握 | 生産性、品質、AI効果、顧客価値、ROI |
| GitHub Actions / CI | Build/Test時間、Queue時間、成功/失敗、再実行 | CI工程の待ち・失敗・安定性 | 顧客影響、AI効果、事業価値 |
| Deploy / CD | Deploy回数、Deploy時間、失敗、Rollback | 提供頻度と提供工程の安定性 | Deployが顧客価値を生んだか |
| Incident / SRE | 障害件数、重大度、復旧時間、SLO、Error Budget | 信頼性・復旧力 | 開発速度やAIとの因果、売上影響 |
| Issue / Project | 着手、完了、WIP、滞留、仕事の種別 | コーディングだけでなく仕事全体のFlow | 顧客価値、AIの投資効果 |
| AI利用データ | 利用者、利用頻度、Token、Suggestion、Agent実行等 | AIの利用・定着・利用形態 | 生産性向上、正味削減時間、ROI |
| AI provenance | 変更・TaskへのAI関与の記録 | AI関与あり/なしの観測比較の土台 | AIが差の原因だったか |
| 時間計測 / サンプリング | 指示、確認、修正、監督等の人の時間 | AIを含む実作業負荷 | 事業価値、現金利益 |
| Finance / 契約 | AIライセンス、クラウド、研修等の実支出 | 投資コスト・現金支出 | 投資効果 |
| Product Analytics | 利用、機能採用、成功行動、継続等 | 顧客が使ったか・価値を受けたか | 開発改善が原因か |
| CRM / Finance | 売上、粗利、契約、継続、解約等 | 事業・財務成果 | Engineering/AIが原因か |
| Survey / People | DevEx、認知負荷、持続可能性等 | 開発者体験・組織の持続可能性 | Deliveryや売上への因果 |

## 2. 複数ソースを組み合わせて初めて分かること

| 組み合わせ | 得られる分析 | 経営・マネジメント上の価値 |
| --- | --- | --- |
| GitHub + CI | PR→検証→Mergeの工程別の待ち・失敗 | 開発ボトルネックの特定 |
| GitHub + Deploy | 変更から提供までの時間 | Time to Marketの観測 |
| Deploy + Incident | 提供速度と変更失敗・復旧の同時観測 | 速さと品質のトレードオフ確認 |
| Issue + GitHub + Deploy | 着手→実装→提供まで | 仕事全体のFlow |
| AI provenance + GitHub | AI関与あり/なしのCycle Time、PRサイズ等 | AI関与時の開発フローの違いを観測 |
| AI provenance + CI | AI関与変更の検証失敗・再実行等 | AI変更の検証負荷を観測 |
| AI provenance + Incident | AI関与変更と品質シグナル | AI利用拡大時の品質ガード |
| AI provenance + 時間計測 | 指示・確認・修正込みの人の作業時間 | AIが人の時間を減らしているかの検証材料 |
| 正味削減時間 + AI Cost | 時間価値、損益分岐、ROI試算 | AI投資判断の参照値 |
| AI + GitHub/Issue + 時間 + Quality | 品質合格まで含めた仕事の完了 | 「生成が速い」ではなく仕事全体が改善したか |
| Engineering + Product Analytics | 提供の変化と顧客利用の関係 | 顧客成果への接続仮説を検証 |
| Product + Finance | 利用・継続と経済成果 | 顧客価値の経済価値化 |
| Engineering + Product + Finance | 開発→提供→利用→事業成果の一連の観測 | Engineering投資を経営へ説明する材料 |

## 3. 生成AIの価値を5段階に分ける

### Level 1: Adoption — 利用・定着

必要データ: AI利用データ。

分かること: 対象用途でAIが使われているか、継続利用されているか。

**分からないこと:** 生産性、ROI、顧客価値。

### Level 2: Execution — AIを使った仕事の進み方

必要データ: AI provenance + GitHub / CI / Issue。

分かること: AI関与あり/なしで、Flow・検証・変更サイズ等がどう違うか。

**分からないこと:** AIが差の原因だったか。

### Level 3: Productivity — 仕事全体が良くなったか

必要データ: AI provenance + Flow + 人の時間 + Quality。

分かること: 指示・確認・修正・統合を含め、品質合格までの仕事が速く・軽くなったか。

### Level 4: Investment Value — 投資に見合うか

必要データ: Level 3 + AI Cost。

分かること: 正味削減時間、キャパシティ価値、損益分岐、ROI試算。

**注意:** キャパシティ価値は現金利益ではない。ROIは仮定を伴う参照値として、感度分析と一緒に扱う。

### Level 5: Business Value — 顧客・事業成果へ届いたか

必要データ: Level 4 + Product Analytics + Finance / CRM。

分かること: 創出されたキャパシティがどこへ再配分され、その先で顧客・事業成果がどう動いたか。

**注意:** データを接続しただけでは因果は確定しない。

## 4. Evidence Level — Taviqが表示する「証拠の強さ」

Taviqは、分析結果に証拠レベルを持たせる。

### 観測

単一または複数のデータソースから直接確認できる事実。

例: 「AI関与PRのCycle Time中央値は20h、非関与PRは30h」。

### 関連

複数データの間で関係・同時変化を確認した状態。

例: 「AI関与変更ではCycle Timeが短い傾向が観測された」。

### 検証中

仕事の種類、難易度、期間、品質条件などを揃え、事前に決めた条件で比較している状態。

### 効果確認

事前に合意した検証条件・判定日・品質ガードを満たし、対象範囲では効果を支持する証拠が得られた状態。

**効果確認でも、対象外への一般化や『AIだけが原因』という断定はしない。**

## 5. データ接続とCapabilityの表示

TaviqのUIは、接続済みソースだけでなく「現在どこまで判断できるか」を表示する。

例:

```text
データ接続

開発
● GitHub
● GitHub Actions
○ Deploy
○ Issue

AI
● AI provenance
○ AI利用データ
○ 人の作業時間
● AI Cost

品質
○ Incident / SLO

顧客
○ Product Analytics

事業
○ CRM / Finance
```

Capability表示:

```text
現在できる分析

✓ Delivery Flow
✓ Review / CI Bottleneck
✓ AI関与変更の観測比較

追加データが必要

△ AI Productivity
  必要: 人の作業時間 + Quality

△ AI ROI
  必要: 正味削減時間 + AI Cost

× AI → Customer Value
  必要: Product Analytics

× AI → Business Value
  必要: Product + Finance
```

## 6. UI・文章生成ルール

Taviqは各分析について次を表示する。

1. **何が観測されたか**
2. **何を意味するか**
3. **証拠レベル**
4. **現時点で言えること**
5. **現時点では言えないこと**
6. **判断に不足しているデータ**
7. **次に何を確認するか**

「未接続」をネガティブなエラーとして隠さない。**どの経営判断に何のデータが不足しているかを示すこと自体を、Taviqの価値とする。**

## 7. KPIマネジメントとの関係

Data Capability Modelは「何が測れるか」を定義する。何を改善目標にするかは別問題である。

TaviqではKPI Playbookの運用原則に沿い、次を分ける。

- KGI: 顧客・事業側の成果
- CSF: 現時点で最優先で強化するプロセス
- 重点KPI: 同時に改善判断をする単位で、その時点で1つ
- カウンターメトリクス: 重点KPI改善の副作用を見張る2〜4指標。目標ではなく閾値を持つ
- 参照値: 全体状況・投資判断・制約変化の確認に使うその他の指標

AI利用率やROI試算を、理由なく重点KPIへ昇格させない。

## 8. Taviqのプロダクト原則

Taviqの価値は「多くの数字を集めること」ではない。

**接続されたデータから、何が言えるか・何がまだ言えないか・次の判断には何が必要かを正確に示すこと。**

最終的に目指すのは、

```text
Engineering data
        ↓
Evidence
        ↓
Meaning
        ↓
Decision
```

であり、Evidenceを飛ばしてDecisionを生成しない。
