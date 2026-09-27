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

def ai_compare(prs):
    a=[p for p in prs if p.get("aiProvenance")=="ai"]
    n=[p for p in prs if p.get("aiProvenance")=="none"]
    missing=len(prs)-len(a)-len(n)
    return summarize(a),summarize(n),((len(a)+len(n))/len(prs)*100 if prs else None),missing

def executive_view(cur,prev,ai=None):
    delivery = change(cur["cycle"], prev["cycle"])
    quality = "Not connected"
    ai_view = "Not provided"
    decision = "Investigate the largest delivery-system change before changing targets."
    if ai:
        r=ai_roi(ai)
        roi="n/a" if r["roi"] is None else f'{r["roi"]:.1f}%'
        ai_view=f'¥{r["cost"]:,.0f} cost → ¥{r["value"]:,.0f} estimated capacity value · ROI {roi}'
        decision="Validate where released AI capacity was redeployed and whether quality guardrails stayed stable."
    return {"delivery":delivery,"quality":quality,"ai":ai_view,"decision":decision}

def html_report(title,since,until,cur,prev,rows,ai=None,compare=None):
    ex=executive_view(cur,prev,ai)
    executive_html=f'''<section class="executive"><div class="eyebrow">EXECUTIVE ENGINEERING REVIEW</div><h2>Investment → Capacity → Delivery → Quality → Business</h2><div class="exec-grid"><div><span>Delivery speed</span><strong>{ex["delivery"]}</strong><small>merge-cycle change</small></div><div><span>Quality guardrail</span><strong>{ex["quality"]}</strong><small>connect CFR / defects next</small></div><div><span>AI investment value</span><strong>{html.escape(ex["ai"])}</strong><small>capacity estimate, not cash profit</small></div></div><div class="decision"><span>DECISION / QUESTION</span><strong>{html.escape(ex["decision"])}</strong></div></section>'''
    cards=[("PRs",str(cur["pr_count"]),change(cur["pr_count"],prev["pr_count"])),("Cycle",fmt(cur["cycle"],"h"),change(cur["cycle"],prev["cycle"])),("First review",fmt(cur["review"],"h"),change(cur["review"],prev["review"])),(">24h review",fmt(cur["over24"],"%"),change(cur["over24"],prev["over24"]))]
    cards_html="".join(f'<div class="card"><span>{html.escape(k)}</span><strong>{html.escape(v)}</strong><small>{html.escape(d)} vs previous</small></div>' for k,v,d in cards)
    ai_html=""
    if ai:
        r=ai_roi(ai); roi="n/a" if r["roi"] is None else f'{r["roi"]:.1f}%'
        ai_html=f'<section><h2>Generative AI value & ROI</h2><div class="cards"><div class="card"><span>Net time saved</span><strong>{float(ai.get("net_hours_saved",0)):.1f}h</strong></div><div class="card"><span>Capacity value</span><strong>¥{r["value"]:,.0f}</strong></div><div class="card"><span>Program cost</span><strong>¥{r["cost"]:,.0f}</strong></div><div class="card"><span>Estimated ROI</span><strong>{roi}</strong></div></div><p class="meta">Capacity-value estimate, not booked cash profit. Include prompting, checking and rework in net time saved.</p></section>'
    cmp_html=""
    if compare:
        a,n,cov,missing=compare; covs="n/a" if cov is None else f"{cov:.1f}%"
        cmp_html=f'<section><h2>AI-involved vs non-AI changes</h2><p class="meta">Provenance coverage: {covs}; unrecorded: {missing}. Observational, not causal.</p><table><tr><th>Condition</th><th>PRs</th><th>Cycle</th><th>Review</th><th>Size</th></tr><tr><td>AI involved</td><td>{a["pr_count"]}</td><td>{fmt(a["cycle"],"h")}</td><td>{fmt(a["review"],"h")}</td><td>{fmt(a["size"])}</td></tr><tr><td>No AI recorded</td><td>{n["pr_count"]}</td><td>{fmt(n["cycle"],"h")}</td><td>{fmt(n["review"],"h")}</td><td>{fmt(n["size"])}</td></tr></table></section>'
    row_html="".join(f'<tr><td>{html.escape(name)}</td><td>{m["pr_count"]}</td><td>{fmt(m["cycle"],"h")}</td><td>{fmt(m["review"],"h")}</td><td>{fmt(m["size"])}</td></tr>' for name,m in rows)
    return f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>{html.escape(title)}</title><style>:root{{color-scheme:dark;font-family:system-ui;background:#0d1117;color:#f0f4f8}}body{{max-width:1100px;margin:auto;padding:48px 28px}}.brand{{letter-spacing:.18em;font-weight:800}}.meta,small{{color:#9aa7b4}}.cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:28px 0}}.card{{border:1px solid #303842;border-radius:14px;padding:18px;background:#121820}}.card span,.card small{{display:block}}.card strong{{display:block;font-size:2rem;margin:8px 0}}section{{margin-top:40px}}table{{width:100%;border-collapse:collapse}}th,td{{padding:12px;text-align:left;border-bottom:1px solid #303842}}.guard{{border-left:4px solid #8b98a5;padding:14px 18px;background:#121820}}@media(max-width:760px){{.cards{{grid-template-columns:1fr 1fr}}}}@media print{{:root{{color-scheme:light;background:white;color:black}}body{{padding:10mm}}}}</style></head><body><div class="brand">TAVIQ</div><h1>{html.escape(title)}</h1><div class="meta">Engineering Intelligence · {since.date()} – {until.date()}</div>{executive_html}<section><div class="eyebrow">ENGINEERING LEADERS</div><h2>Delivery system signals</h2><div class="cards">{cards_html}</div></section>{ai_html}{cmp_html}<section><div class="eyebrow">DIAGNOSTIC DETAIL</div><h2>Repository breakdown</h2><table><tr><th>Repository</th><th>PRs</th><th>Cycle</th><th>Review</th><th>Size</th></tr>{row_html}</table></section><section class="guard"><strong>Interpretation</strong><p>Use these metrics to inspect the delivery system, not to rank individuals. Changes are signals to investigate, not proof of cause.</p></section></body></html>'''

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",action="append",type=Path,required=True); p.add_argument("--repo",action="append",required=True)
    p.add_argument("--since",required=True); p.add_argument("--until"); p.add_argument("--output",type=Path)
    p.add_argument("--format",choices=("html","json"),default="html"); p.add_argument("--title",default="Engineering Delivery Review")
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
