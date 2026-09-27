#!/usr/bin/env python3
from __future__ import annotations
import argparse, html, json, statistics
from datetime import datetime, timezone
from pathlib import Path

def time(v):
    return datetime.fromisoformat(v.replace("Z","+00:00")) if v else None

def hours(a,b):
    a,b=time(a),time(b)
    return (b-a).total_seconds()/3600 if a and b else None

def first_review(pr):
    xs=[x.get("submittedAt") for x in pr.get("reviews",[]) if x.get("submittedAt")]
    return min(xs) if xs else None

def med(xs): return statistics.median(xs) if xs else None
def fmt(v,s=""): return "n/a" if v is None else f"{v:.1f}{s}"
def change(a,b):
    return "n/a" if a is None or b in (None,0) else f"{(a-b)/b*100:+.1f}%"

def summarize(prs):
    cycle=[v for p in prs if p.get("mergedAt") and (v:=hours(p.get("createdAt"),p.get("mergedAt"))) is not None]
    review=[v for p in prs if (v:=hours(p.get("createdAt"),first_review(p))) is not None]
    size=[float(p.get("additions",0)+p.get("deletions",0)) for p in prs if isinstance(p.get("additions",0),(int,float)) and isinstance(p.get("deletions",0),(int,float))]
    return {"pr_count":len(prs),"merged_count":sum(bool(p.get("mergedAt")) for p in prs),"cycle":med(cycle),"review":med(review),"size":med(size),"over24":sum(v>24 for v in review)/len(review)*100 if review else None}

def periods(prs,since,until):
    span=until-since
    cur=[p for p in prs if (t:=time(p.get("createdAt"))) and since<=t<until]
    prev=[p for p in prs if (t:=time(p.get("createdAt"))) and since-span<=t<since]
    return cur,prev

def ai_roi(x):
    cost=float(x.get("seats",0))*float(x.get("license_cost",0))+float(x.get("other_cost",0))
    value=float(x.get("net_hours_saved",0))*float(x.get("loaded_hourly_cost",0))
    return {"cost":cost,"value":value,"net":value-cost,"roi":(value-cost)/cost*100 if cost else None}

def ai_roi_scenarios(x):
    base = ai_roi(x)
    hours = float(x.get("net_hours_saved", 0))
    rate = float(x.get("loaded_hourly_cost", 0))
    cost = base["cost"]
    def scenario(mult):
        value = hours * mult * rate
        return {"hours": hours * mult, "value": value, "roi": (value - cost) / cost * 100 if cost else None}
    break_even_hours = cost / rate if rate else None
    return {"conservative": scenario(0.6), "base": scenario(1.0), "upside": scenario(1.4), "break_even_hours": break_even_hours}

def ai_compare(prs):
    a=[p for p in prs if p.get("aiProvenance")=="ai"]
    n=[p for p in prs if p.get("aiProvenance")=="none"]
    missing=len(prs)-len(a)-len(n)
    return summarize(a),summarize(n),((len(a)+len(n))/len(prs)*100 if prs else None),missing

def executive_view(cur,prev,ai=None):
    delivery_value = change(cur["cycle"], prev["cycle"])
    delivery = {
        "title":"デリバリー",
        "value":delivery_value,
        "meaning":"変更を届けるまでの時間が、前期間から変化しています。",
        "why":"デリバリー speed affects how quickly the organization can respond to customers, market changes, and product learning.",
        "decision":"増員を判断する前に、開発フローのどこで時間がかかっているか確認します。",
    }
    quality = {
        "title":"品質",
        "value":"未接続",
        "meaning":"変更失敗率や流出障害などの品質データがまだ接続されていません。",
        "why":"開発が速くなっても、障害・手戻り・顧客影響が増えていれば生産性向上とは言えません。",
        "decision":"デリバリー速度を改善の根拠にする前に、品質指標を接続します。",
    }
    ai_card = {
        "title":"生成AI投資",
        "value":"未入力",
        "meaning":"この期間のAI費用と正味削減時間が入力されていません。",
        "why":"AIの利用率だけでは、投資が有用な開発キャパシティを生んだか分かりません。",
        "decision":"指示・確認・修正・監督を含めた、人の正味削減時間を測定します。",
    }
    if ai:
        r=ai_roi(ai); roi="n/a" if r["roi"] is None else f'{r["roi"]:.1f}%'
        ai_card={
            "title":"生成AI投資",
            "value":f'ROI {roi}',
            "meaning":f'¥{r["cost"]:,.0f} of declared AI cost is compared with ¥{r["value"]:,.0f} of estimated capacity value.',
            "why":"This tests whether AI spend may be releasing economically meaningful capacity instead of merely increasing tool usage.",
            "decision":"Verify where the released capacity was redeployed and whether delivery, quality, or customer outcomes improved.",
        }
    business = {
        "title":"事業成果",
        "value":"未接続",
        "meaning":"開発組織の変化とプロダクト・事業成果がまだ接続されていません。",
        "why":"キャパシティ増加や高速化だけでは、顧客価値や財務成果につながったとは判断できません。",
        "decision":"投資目的に対応する利用率・売上・継続率・コスト・重要施策などを接続します。",
    }
    return [delivery,quality,ai_card,business]

def monthly_conclusion(cur,prev,ai=None):
    statements=[]
    unknowns=[]
    decisions=[]
    if cur["cycle"] is not None and prev["cycle"] not in (None,0):
        pct=(cur["cycle"]-prev["cycle"])/prev["cycle"]*100
        if pct <= -10:
            statements.append(f"変更を届けるまでの時間は前期間より{abs(pct):.1f}%短縮しています。")
        elif pct >= 10:
            statements.append(f"変更を届けるまでの時間は前期間より{pct:.1f}%長くなっています。")
        else:
            statements.append("変更を届けるまでの時間に大きな変化は見られません。")
    else:
        unknowns.append("デリバリー速度は比較データが不足しており判断できません。")
    unknowns.append("品質データが未接続のため、速度変化が品質を犠牲にしていないかは判断できません。")
    unknowns.append("事業成果が未接続のため、開発改善が顧客価値や財務成果につながったかは判断できません。")
    if ai:
        r=ai_roi(ai)
        if r["net"] > 0:
            statements.append(f"生成AIは時間価値ベースで費用を上回る推計です（純便益 ¥{r['net']:,.0f}）。")
        else:
            statements.append(f"生成AIは時間価値ベースで費用を上回っていません（純便益 ¥{r['net']:,.0f}）。")
        decisions.append("AIで創出された時間が、開発・品質改善・顧客対応のどこへ再配分されたか確認します。")
    decisions.append("品質指標と事業成果を接続し、速度やAI投資の改善が実際の成果につながったか確認します。")
    headline = statements[0] if statements else "現時点では結論に必要なデータが不足しています。"
    return headline,statements,unknowns,decisions

def management_model(cur, prev, ai=None):
    refs = [("PR数", str(cur["pr_count"])), ("初回レビュー", fmt(cur["review"], "h")), ("PRサイズ", fmt(cur["size"], "行"))]
    if ai:
        r = ai_roi(ai)
        refs.append(("AI正味削減時間", f'{float(ai.get("net_hours_saved", 0)):.1f}h'))
        refs.append(("AI ROI試算", "n/a" if r["roi"] is None else f'{r["roi"]:.1f}%'))
    return {
        "kgi": "顧客・事業成果：未接続",
        "hypothesis": "提供までの滞留を減らすと、顧客が価値を受け取る時期を早められる、という検証前の仮説。",
        "csf": "提供までの滞留を減らし、品質を保って届ける",
        "kpi_name": "変更を届けるまでの時間",
        "kpi_value": fmt(cur["cycle"], "h"),
        "kpi_change": change(cur["cycle"], prev["cycle"]),
        "guardrails": [("変更失敗率", "未接続"), ("修正に費やす工数率", "未接続"), ("稼働の健全性", "未接続")],
        "references": refs,
    }

def html_report(title,since,until,cur,prev,rows,ai=None,compare=None):
    ex=executive_view(cur,prev,ai)
    executive_html='<section><div class="eyebrow">経営向けエンジニアリングレビュー</div><h2>何が変わったか、なぜ重要か、何を判断するか</h2><div class="decision-grid">'+"".join(
        f'<article class="decision-card"><div class="decision-head"><span>{html.escape(x["title"])}</span><strong>{html.escape(x["value"])}</strong></div><div class="decision-row"><b>何を意味する？</b><p>{html.escape(x["meaning"])}</p></div><div class="decision-row"><b>なぜ重要？</b><p>{html.escape(x["why"])}</p></div><div class="decision-row action"><b>次の判断</b><p>{html.escape(x["decision"])}</p></div></article>'
        for x in ex
    )+'</div></section>'
    cards=[("PRs",str(cur["pr_count"]),change(cur["pr_count"],prev["pr_count"])),("Cycle",fmt(cur["cycle"],"h"),change(cur["cycle"],prev["cycle"])),("First review",fmt(cur["review"],"h"),change(cur["review"],prev["review"])),(">24h review",fmt(cur["over24"],"%"),change(cur["over24"],prev["over24"]))]
    cards_html="".join(f'<div class="card"><span>{html.escape(k)}</span><strong>{html.escape(v)}</strong><small>{html.escape(d)} vs previous</small></div>' for k,v,d in cards)
    ai_html=""
    if ai:
        r=ai_roi(ai); scenarios=ai_roi_scenarios(ai)
        def roi_text(v): return "n/a" if v is None else f"{v:.1f}%"
        ai_html=f'''<section class="ai-investment"><div class="eyebrow">生成AI投資 · 参照値</div><h2>ROIは一点ではなく、仮定の幅で判断する</h2><p class="meta">時間価値の試算です。現金利益ではありません。AI利用費に加え、人の指示・確認・修正・研修・運用負担を費用側で確認します。</p><div class="scenario-grid"><div><span>控えめ</span><strong>{roi_text(scenarios["conservative"]["roi"])}</strong><small>{scenarios["conservative"]["hours"]:.1f}hの正味削減を仮定</small></div><div class="base-scenario"><span>基準試算</span><strong>{roi_text(scenarios["base"]["roi"])}</strong><small>{scenarios["base"]["hours"]:.1f}h · 価値 ¥{scenarios["base"]["value"]:,.0f}</small></div><div><span>良い場合</span><strong>{roi_text(scenarios["upside"]["roi"])}</strong><small>{scenarios["upside"]["hours"]:.1f}hの正味削減を仮定</small></div></div><div class="assumption-grid"><div><b>損益分岐</b><strong>{"n/a" if scenarios["break_even_hours"] is None else f'{scenarios["break_even_hours"]:.1f}h'}</strong><p>この正味削減時間を下回ると、時間価値ベースの純便益はマイナス。</p></div><div><b>時間価値</b><strong>¥{r["value"]:,.0f}</strong><p>削減時間 × loaded hourly cost。現金支出の削減とは別。</p></div><div><b>現金効果</b><strong>未接続</strong><p>実際に減った契約・請求・人件費等がある場合のみ別途計上。</p></div></div><div class="assumption-note"><b>仮定として残すもの</b><p>正味削減時間、時間単価、学習期間、品質への影響。どの仮定を変えると結論が反転するかを確認し、次回測り直す担当と日付を残します。</p></div></section>'''
    cmp_html=""
    if compare:
        a,n,cov,missing=compare; covs="n/a" if cov is None else f"{cov:.1f}%"
        cmp_html=f'<section><h2>AI関与あり・なしの比較</h2><p class="meta">AI関与の記録率: {covs}; unrecorded: {missing}. Observational, not causal.</p><table><tr><th>Condition</th><th>PRs</th><th>Cycle</th><th>Review</th><th>Size</th></tr><tr><td>AI involved</td><td>{a["pr_count"]}</td><td>{fmt(a["cycle"],"h")}</td><td>{fmt(a["review"],"h")}</td><td>{fmt(a["size"])}</td></tr><tr><td>No AI recorded</td><td>{n["pr_count"]}</td><td>{fmt(n["cycle"],"h")}</td><td>{fmt(n["review"],"h")}</td><td>{fmt(n["size"])}</td></tr></table></section>'
    row_html="".join(f'<tr><td>{html.escape(name)}</td><td>{m["pr_count"]}</td><td>{fmt(m["cycle"],"h")}</td><td>{fmt(m["review"],"h")}</td><td>{fmt(m["size"])}</td></tr>' for name,m in rows)
    flow_html='<div class="removed-flow"><div><span>INVEST</span><strong>Engineering</strong></div><b>→</b><div><span>UNLOCK</span><strong>Capacity</strong></div><b>→</b><div><span>SHIP</span><strong>デリバリー</strong></div><b>→</b><div><span>PROTECT</span><strong>品質</strong></div><b>→</b><div><span>CREATE</span><strong>Business value</strong></div></div>'
    return f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>{html.escape(title)}</title><style>
:root{{color-scheme:dark;font-family:Inter,ui-sans-serif,system-ui,sans-serif;background:#080b10;color:#f5f7fa;--panel:#10151d;--line:#27303b;--muted:#8e9baa;--accent:#d7ff64}}*{{box-sizing:border-box}}body{{max-width:1180px;margin:auto;padding:56px 32px;background:radial-gradient(circle at 80% 0%,#18221d 0,transparent 32%)}}.brand{{display:inline-flex;align-items:center;gap:10px;letter-spacing:.2em;font-weight:900;font-size:.85rem}}.brand:before{{content:"";width:10px;height:10px;border-radius:3px;background:var(--accent);box-shadow:0 0 24px var(--accent)}}h1{{font-size:clamp(2.4rem,6vw,4.8rem);line-height:.95;letter-spacing:-.06em;max-width:850px;margin:20px 0 14px}}h2{{font-size:1.45rem;letter-spacing:-.025em;margin:8px 0 18px}}.meta,small,.eyebrow{{color:var(--muted)}}.eyebrow{{font-size:.72rem;letter-spacing:.16em}}section{{margin-top:52px}}.executive{{padding:28px;border:1px solid var(--line);border-radius:20px;background:linear-gradient(145deg,#151b24,var(--panel));box-shadow:0 24px 80px rgba(0,0,0,.22)}}.exec-grid,.cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-top:22px}}.exec-grid{{grid-template-columns:1fr 1fr 2fr}}.exec-grid>div,.card{{padding:20px;background:#0b1016;border:1px solid #202833;border-radius:14px}}.exec-grid span,.exec-grid small,.card span,.card small,.decision span{{display:block;color:var(--muted)}}.exec-grid strong{{display:block;margin:8px 0;font-size:1.1rem}}.card strong{{display:block;font-size:clamp(1.55rem,3vw,2.4rem);letter-spacing:-.04em;margin:10px 0}}.decision{{margin-top:18px;padding:18px 20px;border-left:4px solid var(--accent);background:#0b1016;border-radius:0 12px 12px 0}}.decision strong{{display:block;margin-top:8px}}.flow{{display:grid;grid-template-columns:1fr auto 1fr auto 1fr auto 1fr auto 1fr;align-items:center;gap:10px;margin:30px 0 8px}}.flow div{{padding:16px;border:1px solid var(--line);border-radius:14px;background:var(--panel)}}.flow span{{display:block;color:var(--muted);font-size:.65rem;letter-spacing:.12em}}.flow strong{{display:block;margin-top:6px}}.flow b{{color:var(--accent)}}table{{width:100%;border-collapse:separate;border-spacing:0;background:var(--panel);border:1px solid var(--line);border-radius:14px;overflow:hidden}}th,td{{padding:14px 16px;text-align:left;border-bottom:1px solid var(--line)}}th{{font-size:.72rem;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);background:#0c1117}}tr:last-child td{{border-bottom:0}}.guard{{border:1px solid var(--line);border-left:4px solid var(--accent);padding:18px 22px;background:var(--panel);border-radius:0 14px 14px 0}}@media(max-width:760px){{body{{padding:32px 18px}}.cards,.exec-grid,.flow{{grid-template-columns:1fr}}.flow b{{display:none}}table{{display:block;overflow-x:auto}}}}@media print{{:root{{color-scheme:light;background:white;color:black}}body{{padding:10mm;background:white}}}}
</style></head><body><div class="brand">TAVIQ</div><h1>{html.escape(title)}</h1><div class="meta">Engineering Intelligence · {since.date()} – {until.date()}</div>{conclusion_html}{management_html}<section><div class="eyebrow">開発組織向け</div><h2>デリバリー system signals</h2><div class="cards">{cards_html}</div></section>{ai_html}{cmp_html}<section><div class="eyebrow">診断詳細</div><h2>リポジトリ別内訳</h2><table><tr><th>Repository</th><th>PRs</th><th>Cycle</th><th>Review</th><th>Size</th></tr>{row_html}</table></section><section class="guard"><strong>読み方</strong><p>これらの指標は開発システムを改善するために使い、個人の順位付けには使いません。変化は調査の手掛かりであり、原因を証明するものではありません。</p></section></body></html>'''/usr/bin/env python3
from __future__ import annotations
import argparse, html, json, statistics
from datetime import datetime, timezone
from pathlib import Path

def time(v):
    return datetime.fromisoformat(v.replace("Z","+00:00")) if v else None

def hours(a,b):
    a,b=time(a),time(b)
    return (b-a).total_seconds()/3600 if a and b else None

def first_review(pr):
    xs=[x.get("submittedAt") for x in pr.get("reviews",[]) if x.get("submittedAt")]
    return min(xs) if xs else None

def med(xs): return statistics.median(xs) if xs else None
def fmt(v,s=""): return "n/a" if v is None else f"{v:.1f}{s}"
def change(a,b):
    return "n/a" if a is None or b in (None,0) else f"{(a-b)/b*100:+.1f}%"

def summarize(prs):
    cycle=[v for p in prs if p.get("mergedAt") and (v:=hours(p.get("createdAt"),p.get("mergedAt"))) is not None]
    review=[v for p in prs if (v:=hours(p.get("createdAt"),first_review(p))) is not None]
    size=[float(p.get("additions",0)+p.get("deletions",0)) for p in prs if isinstance(p.get("additions",0),(int,float)) and isinstance(p.get("deletions",0),(int,float))]
    return {"pr_count":len(prs),"merged_count":sum(bool(p.get("mergedAt")) for p in prs),"cycle":med(cycle),"review":med(review),"size":med(size),"over24":sum(v>24 for v in review)/len(review)*100 if review else None}

def periods(prs,since,until):
    span=until-since
    cur=[p for p in prs if (t:=time(p.get("createdAt"))) and since<=t<until]
    prev=[p for p in prs if (t:=time(p.get("createdAt"))) and since-span<=t<since]
    return cur,prev

def ai_roi(x):
    cost=float(x.get("seats",0))*float(x.get("license_cost",0))+float(x.get("other_cost",0))
    value=float(x.get("net_hours_saved",0))*float(x.get("loaded_hourly_cost",0))
    return {"cost":cost,"value":value,"net":value-cost,"roi":(value-cost)/cost*100 if cost else None}

def ai_compare(prs):
    a=[p for p in prs if p.get("aiProvenance")=="ai"]
    n=[p for p in prs if p.get("aiProvenance")=="none"]
    missing=len(prs)-len(a)-len(n)
    return summarize(a),summarize(n),((len(a)+len(n))/len(prs)*100 if prs else None),missing

def executive_view(cur,prev,ai=None):
    delivery = change(cur["cycle"], prev["cycle"])
    quality = "未接続"
    ai_view = "未入力"
    decision = "Investigate the largest delivery-system change before changing targets."
    if ai:
        r=ai_roi(ai)
        roi="n/a" if r["roi"] is None else f'{r["roi"]:.1f}%'
        ai_view=f'¥{r["cost"]:,.0f} cost → ¥{r["value"]:,.0f} estimated capacity value · ROI {roi}'
        decision="Validate where released AI capacity was redeployed and whether quality guardrails stayed stable."
    return {"delivery":delivery,"quality":quality,"ai":ai_view,"decision":decision}

def html_report(title,since,until,cur,prev,rows,ai=None,compare=None):
    ex=executive_view(cur,prev,ai)
    executive_html=f'''<section class="executive"><div class="eyebrow">経営向けエンジニアリングレビュー</div><h2>Investment → Capacity → デリバリー → 品質 → Business</h2><div class="exec-grid"><div><span>デリバリー speed</span><strong>{ex["delivery"]}</strong><small>merge-cycle change</small></div><div><span>品質 guardrail</span><strong>{ex["quality"]}</strong><small>connect CFR / defects next</small></div><div><span>AI investment value</span><strong>{html.escape(ex["ai"])}</strong><small>capacity estimate, not cash profit</small></div></div><div class="decision"><span>次の判断 / QUESTION</span><strong>{html.escape(ex["decision"])}</strong></div></section>'''
    cards=[("PRs",str(cur["pr_count"]),change(cur["pr_count"],prev["pr_count"])),("Cycle",fmt(cur["cycle"],"h"),change(cur["cycle"],prev["cycle"])),("First review",fmt(cur["review"],"h"),change(cur["review"],prev["review"])),(">24h review",fmt(cur["over24"],"%"),change(cur["over24"],prev["over24"]))]
    cards_html="".join(f'<div class="card"><span>{html.escape(k)}</span><strong>{html.escape(v)}</strong><small>{html.escape(d)} vs previous</small></div>' for k,v,d in cards)
    ai_html=""
    if ai:
        r=ai_roi(ai); roi="n/a" if r["roi"] is None else f'{r["roi"]:.1f}%'
        ai_html=f'<section><h2>生成AIの価値・ROI</h2><div class="cards"><div class="card"><span>正味削減時間</span><strong>{float(ai.get("net_hours_saved",0)):.1f}h</strong></div><div class="card"><span>キャパシティ価値</span><strong>¥{r["value"]:,.0f}</strong></div><div class="card"><span>AI費用</span><strong>¥{r["cost"]:,.0f}</strong></div><div class="card"><span>推計ROI</span><strong>{roi}</strong></div></div><p class="meta">Capacity-value estimate, not booked cash profit. Include prompting, checking and rework in net time saved.</p></section>'
    cmp_html=""
    if compare:
        a,n,cov,missing=compare; covs="n/a" if cov is None else f"{cov:.1f}%"
        cmp_html=f'<section><h2>AI関与あり・なしの比較</h2><p class="meta">AI関与の記録率: {covs}; unrecorded: {missing}. Observational, not causal.</p><table><tr><th>Condition</th><th>PRs</th><th>Cycle</th><th>Review</th><th>Size</th></tr><tr><td>AI involved</td><td>{a["pr_count"]}</td><td>{fmt(a["cycle"],"h")}</td><td>{fmt(a["review"],"h")}</td><td>{fmt(a["size"])}</td></tr><tr><td>No AI recorded</td><td>{n["pr_count"]}</td><td>{fmt(n["cycle"],"h")}</td><td>{fmt(n["review"],"h")}</td><td>{fmt(n["size"])}</td></tr></table></section>'
    row_html="".join(f'<tr><td>{html.escape(name)}</td><td>{m["pr_count"]}</td><td>{fmt(m["cycle"],"h")}</td><td>{fmt(m["review"],"h")}</td><td>{fmt(m["size"])}</td></tr>' for name,m in rows)
    return f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>{html.escape(title)}</title><style>:root{{color-scheme:dark;font-family:system-ui;background:#0d1117;color:#f0f4f8}}body{{max-width:1100px;margin:auto;padding:48px 28px}}.brand{{letter-spacing:.18em;font-weight:800}}.meta,small{{color:#9aa7b4}}.cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:28px 0}}.card{{border:1px solid #303842;border-radius:14px;padding:18px;background:#121820}}.card span,.card small{{display:block}}.card strong{{display:block;font-size:2rem;margin:8px 0}}section{{margin-top:40px}}table{{width:100%;border-collapse:collapse}}th,td{{padding:12px;text-align:left;border-bottom:1px solid #303842}}.guard{{border-left:4px solid #8b98a5;padding:14px 18px;background:#121820}}@media(max-width:760px){{.cards{{grid-template-columns:1fr 1fr}}}}@media print{{:root{{color-scheme:light;background:white;color:black}}body{{padding:10mm}}}}</style></head><body><div class="brand">TAVIQ</div><h1>{html.escape(title)}</h1><div class="meta">Engineering Intelligence · {since.date()} – {until.date()}</div>{executive_html}<section><div class="eyebrow">開発組織向け</div><h2>デリバリー system signals</h2><div class="cards">{cards_html}</div></section>{ai_html}{cmp_html}<section><div class="eyebrow">診断詳細</div><h2>リポジトリ別内訳</h2><table><tr><th>Repository</th><th>PRs</th><th>Cycle</th><th>Review</th><th>Size</th></tr>{row_html}</table></section><section class="guard"><strong>読み方</strong><p>Use these metrics to inspect the delivery system, not to rank individuals. Changes are signals to investigate, not proof of cause.</p></section></body></html>'''

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",action="append",type=Path,required=True); p.add_argument("--repo",action="append",required=True)
    p.add_argument("--since",required=True); p.add_argument("--until"); p.add_argument("--output",type=Path)
    p.add_argument("--format",choices=("html","json"),default="html"); p.add_argument("--title",default="Engineering デリバリー Review")
    p.add_argument("--ai-input",type=Path); a=p.parse_args()
    if len(a.input)!=len(a.repo): p.error("--input and --repo counts must match")
    since=datetime.fromisoformat(a.since).replace(tzinfo=timezone.utc); until=datetime.fromisoformat(a.until).replace(tzinfo=timezone.utc) if a.until else datetime.now(timezone.utc)
    all_cur=[]; all_prev=[]; rows=[]
    for path,name in zip(a.input,a.repo):
        prs=json.loads(path.read_text()); cur,prev=periods(prs,since,until); all_cur+=cur; all_prev+=prev; rows.append((name,summarize(cur)))
    cur,prev=summarize(all_cur),summarize(all_prev); ai=json.loads(a.ai_input.read_text()) if a.ai_input else None
    cmp=ai_compare(all_cur) if any("aiProvenance" in x for x in all_cur) else None
    out=html_report(a.title,since,until,cur,prev,rows,ai,cmp) if a.format=="html" else json.dumps({"current":cur,"previous":prev},ensure_ascii=False,indent=2)
    if a.output: a.output.write_text(out)
    else: print(out)
if __name__=="__main__": main()
