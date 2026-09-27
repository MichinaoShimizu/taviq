#!/usr/bin/env python3
"""Convert ephemeral Taviq runtime observations into Basic commit trailers."""
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
    if not p or not p.exists(): return {}
    try: return json.loads(p.read_text())
    except Exception: return {}

def values(runtime,env):
    tools=set(runtime.get("tools",[])); modes=set(runtime.get("modes",[])); models=set(runtime.get("models",[]))
    if env.get("TAVIQ_TOOL"): tools.add(env["TAVIQ_TOOL"])
    if env.get("TAVIQ_MODE") in ALLOWED_MODES: modes.add(env["TAVIQ_MODE"])
    if env.get("TAVIQ_MODEL"): models.add(env["TAVIQ_MODEL"])
    return sorted(tools),sorted(m for m in modes if m in ALLOWED_MODES),sorted(models)

def trailer_lines(runtime,env):
    tools,modes,models=values(runtime,env)
    if not tools: return []
    lines=["Taviq-Provenance: v1","Taviq-Tools: "+",".join(tools)]
    if modes: lines.append("Taviq-Modes: "+",".join(modes))
    if models: lines.append("Taviq-Models: "+",".join(models))
    return lines

def clear_runtime():
    p=runtime_path()
    if p and p.exists(): p.unlink()

def apply(path,env=os.environ):
    started=time.perf_counter()
    lines=trailer_lines(load_runtime(),env)
    if not lines: return {"applied":False,"elapsed_ms":(time.perf_counter()-started)*1000,"metadata_bytes":0}
    p=Path(path); text=p.read_text()
    if "Taviq-Provenance:" in text: return {"applied":False,"elapsed_ms":(time.perf_counter()-started)*1000,"metadata_bytes":0}
    trailer="\n".join(lines)+"\n"
    suffix="\n" if text.endswith("\n") else "\n\n"
    p.write_text(text+suffix+trailer)
    clear_runtime()
    return {"applied":True,"elapsed_ms":(time.perf_counter()-started)*1000,"metadata_bytes":len(trailer.encode("utf-8"))}

if __name__=="__main__":
    if len(sys.argv)<2: raise SystemExit("commit message path required")
    apply(sys.argv[1])