#!/usr/bin/env python3
"""Convert ephemeral Taviq runtime observations into minimal commit trailers."""
import json, os, subprocess, sys, time
from pathlib import Path

ALLOWED_MODES={"assist","generate","agent","crew","mixed"}

def repo_root():
    try:
        return Path(subprocess.check_output(["git","rev-parse","--show-toplevel"],text=True,stderr=subprocess.DEVNULL).strip())
    except Exception:
        return None

def runtime_path():
    root=repo_root()
    return root/".taviq"/"runtime.json" if root else None

def load_runtime():
    p=runtime_path()
    if not p or not p.exists(): return {"tools":[],"modes":[],"models":[]}
    try: x=json.loads(p.read_text())
    except Exception: return {"tools":[],"modes":[],"models":[]}
    # Backward compatibility with pre-multi-value runtime.
    if "tool" in x:
        x={"tools":[x["tool"]],"modes":[x["mode"]] if x.get("mode") else [],"models":[x["model"]] if x.get("model") else []}
    return {
        "tools":sorted(set(v for v in x.get("tools",[]) if isinstance(v,str) and v)),
        "modes":sorted(set(v for v in x.get("modes",[]) if v in ALLOWED_MODES)),
        "models":sorted(set(v for v in x.get("models",[]) if isinstance(v,str) and v)),
    }

def observations(env=os.environ):
    x=load_runtime()
    if env.get("TAVIQ_TOOL"): x["tools"]=sorted(set(x["tools"]+[env["TAVIQ_TOOL"]]))
    if env.get("TAVIQ_MODE") in ALLOWED_MODES: x["modes"]=sorted(set(x["modes"]+[env["TAVIQ_MODE"]]))
    if env.get("TAVIQ_MODEL"): x["models"]=sorted(set(x["models"]+[env["TAVIQ_MODEL"]]))
    return x

def trailer_lines(obs):
    if not obs["tools"]: return []
    lines=["Taviq-Provenance: v1","Taviq-Tools: "+",".join(obs["tools"])]
    if obs["modes"]: lines.append("Taviq-Modes: "+",".join(obs["modes"]))
    if obs["models"]: lines.append("Taviq-Models: "+",".join(obs["models"]))
    return lines

def clear_runtime():
    p=runtime_path()
    if p and p.exists(): p.unlink()

def apply(path,env=os.environ):
    started=time.perf_counter()
    lines=trailer_lines(observations(env))
    if not lines:
        return {"applied":False,"elapsed_ms":(time.perf_counter()-started)*1000,"metadata_bytes":0}
    p=Path(path); text=p.read_text()
    if "Taviq-Provenance:" in text:
        return {"applied":False,"elapsed_ms":(time.perf_counter()-started)*1000,"metadata_bytes":0}
    trailer="\n".join(lines)+"\n"
    suffix="\n" if text.endswith("\n") else "\n\n"
    p.write_text(text+suffix+trailer)
    clear_runtime()
    return {"applied":True,"elapsed_ms":(time.perf_counter()-started)*1000,"metadata_bytes":len(trailer.encode())}

if __name__=="__main__":
    if len(sys.argv)<2: raise SystemExit("commit message path required")
    apply(sys.argv[1])
