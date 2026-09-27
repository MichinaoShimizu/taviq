#!/usr/bin/env python3
import argparse, json, re, subprocess
from pathlib import Path

KEYS={"Taviq-Provenance":"version","Taviq-Tools":"tools","Taviq-Modes":"modes","Taviq-Models":"models","Taviq-Agents":"agents"}

def split_values(value):
    return sorted(set(v.strip() for v in (value or "").split(",") if v.strip()))

TRAILER=re.compile(r"^[A-Za-z0-9][A-Za-z0-9-]*:( |$)")
LEGACY={"Taviq-Tool":"tools","Taviq-Mode":"modes","Taviq-Model":"models"}

def blocks(body):
    """Provenance blocks: paragraphs whose lines are all trailers and include a Taviq field.

    Squash merges leave each commit's trailer paragraph in the body, so blocks are
    read from the whole message, not only the final trailer paragraph.
    """
    out=[]
    for para in re.split(r"\n\s*\n",body):
        lines=[l.strip() for l in para.splitlines() if l.strip()]
        if lines and all(TRAILER.match(l) for l in lines):
            fields=[l for l in lines if l.split(":",1)[0] in KEYS or l.split(":",1)[0] in LEGACY]
            if fields: out.append(fields)
    return out

def parse(body):
    found={}
    for block in blocks(body):
        legacy={}
        for line in block:
            prefix,raw=line.split(":",1)
            raw=raw.strip()
            if prefix in KEYS:
                key=KEYS[prefix]
                if key=="version": found.setdefault("version",raw)
                else: found[key]=sorted(set(found.get(key,[]))|set(split_values(raw)))
            else:
                legacy.setdefault(LEGACY[prefix],[raw])
        # Backward-compatible legacy single-value trailers.
        for key,values in legacy.items():
            if key not in found: found[key]=values
    return found

def trailers(repo,base,head):
    shas=subprocess.check_output(["git","-C",str(repo),"rev-list",f"{base}..{head}"],text=True).split()
    rows=[]
    for sha in shas:
        body=subprocess.check_output(["git","-C",str(repo),"show","-s","--format=%B",sha],text=True)
        found=parse(body)
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
        "agents":counts("agents"),
        "multi_tool_commits":sum(1 for r in recorded if len(r.get("tools",[]))>1),
    }

def main():
    p=argparse.ArgumentParser(); p.add_argument("--repo",type=Path,default=Path(".")); p.add_argument("--base",required=True); p.add_argument("--head",required=True)
    a=p.parse_args(); rows=trailers(a.repo,a.base,a.head); print(json.dumps({"summary":summarize(rows),"commits":rows},ensure_ascii=False,indent=2))
if __name__=="__main__": main()
