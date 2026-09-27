#!/usr/bin/env python3
import argparse, hashlib, hmac, json, os, subprocess
from pathlib import Path

KEYS={"Taviq-Provenance":"version","Taviq-Tool":"tool","Taviq-Mode":"mode","Taviq-Model":"model","Taviq-Ref":"ref","Taviq-Signature":"signature"}

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

def verify_row(row,repository,key):
    sig=row.get("signature","")
    if not key or not sig.startswith("hmac-sha256:") or not row.get("ref"):
        return "unverified" if row.get("version") else "unknown"
    payload={k:row.get(k,"") for k in ("version","tool","mode","model","ref")}
    payload["repository"]=repository
    canonical="\\n".join(f"{k}={payload[k]}" for k in ("version","tool","mode","model","repository","ref")).encode()
    expected=hmac.new(key.encode(),canonical,hashlib.sha256).hexdigest()
    return "verified" if hmac.compare_digest(expected,sig.split(":",1)[1]) else "invalid"

def summarize(rows):
    confirmed=[r for r in rows if r["status"]=="confirmed"]
    return {"commits":len(rows),"confirmed":len(confirmed),"unknown":len(rows)-len(confirmed),"coverage":len(confirmed)/len(rows)*100 if rows else None,"tools":sorted(set(r.get("tool") for r in confirmed if r.get("tool"))),"modes":sorted(set(r.get("mode") for r in confirmed if r.get("mode"))),"models":sorted(set(r.get("model") for r in confirmed if r.get("model")))}

def main():
    p=argparse.ArgumentParser(); p.add_argument("--repo",type=Path,default=Path(".")); p.add_argument("--base",required=True); p.add_argument("--head",required=True); p.add_argument("--repository",default=os.environ.get("GITHUB_REPOSITORY",""))
    a=p.parse_args(); rows=trailers(a.repo,a.base,a.head); key=os.environ.get("TAVIQ_SIGNING_KEY");\n    for row in rows: row["verification"]=verify_row(row,a.repository,key)\n    print(json.dumps({"summary":summarize(rows),"commits":rows},ensure_ascii=False,indent=2))
if __name__=="__main__": main()
