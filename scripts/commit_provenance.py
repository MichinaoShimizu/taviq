#!/usr/bin/env python3
import argparse, json, subprocess
from pathlib import Path

KEYS={"Taviq-Provenance":"version","Taviq-Tools":"tools","Taviq-Modes":"modes","Taviq-Models":"models"}

def split_values(value):
    return sorted(set(v.strip() for v in (value or "").split(",") if v.strip()))

def trailers(repo,base,head):
    shas=subprocess.check_output(["git","-C",str(repo),"rev-list",f"{base}..{head}"],text=True).split()
    rows=[]
    for sha in shas:
        body=subprocess.check_output(["git","-C",str(repo),"show","-s","--format=%B",sha],text=True)
        found={}
        for line in body.splitlines():
            for prefix,key in KEYS.items():
                mark=prefix+":"
                if line.startswith(mark):
                    raw=line[len(mark):].strip()
                    found[key]=split_values(raw) if key in ("tools","modes","models") else raw
        # Backward-compatible legacy single-value trailers.
        legacy={"Taviq-Tool":"tools","Taviq-Mode":"modes","Taviq-Model":"models"}
        for line in body.splitlines():
            for prefix,key in legacy.items():
                mark=prefix+":"
                if line.startswith(mark) and key not in found: found[key]=[line[len(mark):].strip()]
        rows.append({"commit":sha,**found,"status":"recorded" if found.get("version") and found.get("tools") else "unknown"})
    return rows

def summarize(rows):
    recorded=[r for r in rows if r["status"]=="recorded"]
    def counts(field):
        out={}
        for r in recorded:
            for v in r.get(field,[]): out[v]=out.get(v,0)+1
        return dict(sorted(out.items()))
    return {
        "commits":len(rows),
        "recorded":len(recorded),
        "unknown":len(rows)-len(recorded),
        "coverage":len(recorded)/len(rows)*100 if rows else None,
        "tools":counts("tools"),
        "modes":counts("modes"),
        "models":counts("models"),
        "multi_tool_commits":sum(1 for r in recorded if len(r.get("tools",[]))>1),
    }

def main():
    p=argparse.ArgumentParser(); p.add_argument("--repo",type=Path,default=Path(".")); p.add_argument("--base",required=True); p.add_argument("--head",required=True)
    a=p.parse_args(); rows=trailers(a.repo,a.base,a.head); print(json.dumps({"summary":summarize(rows),"commits":rows},ensure_ascii=False,indent=2))
if __name__=="__main__": main()
