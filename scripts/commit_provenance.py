#!/usr/bin/env python3
import argparse, json, subprocess
from pathlib import Path

KEYS={"Taviq-Provenance":"version","Taviq-Tool":"tool","Taviq-Mode":"mode","Taviq-Model":"model"}

def trailers(repo,base,head):
    shas=subprocess.check_output(["git","-C",str(repo),"rev-list",f"{base}..{head}"],text=True).split()
    rows=[]
    for sha in shas:
        body=subprocess.check_output(["git","-C",str(repo),"show","-s","--format=%B",sha],text=True)
        found={}
        for line in body.splitlines():
            for prefix,key in KEYS.items():
                mark=prefix+":"
                if line.startswith(mark): found[key]=line[len(mark):].strip()
        rows.append({"commit":sha,**found,"status":"confirmed" if "version" in found else "unknown"})
    return rows

def summarize(rows):
    confirmed=[r for r in rows if r["status"]=="confirmed"]
    return {"commits":len(rows),"confirmed":len(confirmed),"unknown":len(rows)-len(confirmed),"coverage":len(confirmed)/len(rows)*100 if rows else None,"tools":sorted(set(r.get("tool") for r in confirmed if r.get("tool"))),"modes":sorted(set(r.get("mode") for r in confirmed if r.get("mode"))),"models":sorted(set(r.get("model") for r in confirmed if r.get("model")))}

def main():
    p=argparse.ArgumentParser(); p.add_argument("--repo",type=Path,default=Path(".")); p.add_argument("--base",required=True); p.add_argument("--head",required=True)
    a=p.parse_args(); rows=trailers(a.repo,a.base,a.head); print(json.dumps({"summary":summarize(rows),"commits":rows},ensure_ascii=False,indent=2))
if __name__=="__main__": main()
