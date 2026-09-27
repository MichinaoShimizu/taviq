#!/usr/bin/env python3
import argparse, json, os, subprocess
from pathlib import Path
ALLOWED_TOOLS={"claude","codex","kiro"}
ALLOWED_MODES={"assist","generate","agent","crew","mixed"}
def root(cwd="."):
    try:return Path(subprocess.check_output(["git","-C",cwd,"rev-parse","--show-toplevel"],text=True).strip())
    except Exception:return Path(cwd).resolve()
def write(tool,mode=None,model=None,cwd=".",reset=False):
    if tool not in ALLOWED_TOOLS: raise ValueError("unsupported tool")
    x={"tool":tool}
    if mode in ALLOWED_MODES:x["mode"]=mode
    if model:x["model"]=model
    p=root(cwd)/".taviq"/"runtime.json"; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(x,separators=(",",":"))); return p
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--tool",required=True);p.add_argument("--mode");p.add_argument("--model");p.add_argument("--cwd",default=os.getcwd());p.add_argument("--reset",action="store_true");a=p.parse_args();write(a.tool,a.mode,a.model,a.cwd,a.reset)
