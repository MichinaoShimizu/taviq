#!/usr/bin/env python3
import argparse, json, os, subprocess
from pathlib import Path
ALLOWED_TOOLS={"claude","codex","kiro"}
ALLOWED_MODES={"assist","generate","agent","crew","mixed"}

def root(cwd="."):
    try:
        return Path(subprocess.check_output(["git","-C",cwd,"rev-parse","--show-toplevel"],text=True,stderr=subprocess.DEVNULL).strip())
    except Exception:
        return Path(cwd).resolve()

def head(cwd="."):
    try:
        return subprocess.check_output(["git","-C",cwd,"rev-parse","HEAD"],text=True,stderr=subprocess.DEVNULL).strip()
    except Exception:
        return None

def write(tool,mode=None,model=None,cwd="."):
    if tool not in ALLOWED_TOOLS: raise ValueError("unsupported tool")
    repo=root(cwd); current_head=head(repo)
    p=repo/".taviq"/"runtime.json"; p.parent.mkdir(parents=True,exist_ok=True)
    try: previous=json.loads(p.read_text()) if p.exists() else {}
    except Exception: previous={}
    if previous.get("base_head") != current_head:
        previous={"schema_version":1,"base_head":current_head,"tools":[],"modes":[],"models":[]}
    x={"schema_version":1,"base_head":current_head,"tools":list(previous.get("tools",[])),"modes":list(previous.get("modes",[])),"models":list(previous.get("models",[]))}
    if tool not in x["tools"]: x["tools"].append(tool)
    if mode in ALLOWED_MODES and mode not in x["modes"]: x["modes"].append(mode)
    if model and model not in x["models"]: x["models"].append(model)
    for k in ("tools","modes","models"): x[k]=sorted(set(x[k]))
    p.write_text(json.dumps(x,separators=(",",":"))); return p

def clear(cwd='.'):
    p=root(cwd)/".taviq"/"runtime.json"
    if p.exists(): p.unlink()

if __name__=="__main__":
    p=argparse.ArgumentParser(); p.add_argument('--tool'); p.add_argument('--mode'); p.add_argument('--model'); p.add_argument('--cwd',default=os.getcwd()); p.add_argument('--clear',action='store_true'); a=p.parse_args()
    if a.clear: clear(a.cwd)
    else:
        if not a.tool: raise SystemExit('--tool is required unless --clear is used')
        write(a.tool,a.mode,a.model,a.cwd)