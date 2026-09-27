#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, os, subprocess, sys, uuid
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_HOME = Path(os.environ.get("TAVIQ_HOME", Path.home() / ".taviq"))
ALLOWED_TOP = {"session_id","hook_event_name","event_name","model","model_name","cwd","tool","provider","usage","file_path"}
SENSITIVE_KEYS = {"prompt","response","messages","content","tool_input","tool_output","diff","source","code"}

def now():
    return datetime.now(timezone.utc).isoformat()

def git(cwd, *args):
    try:
        return subprocess.check_output(["git","-C",str(cwd),*args], text=True, stderr=subprocess.DEVNULL).strip() or None
    except Exception:
        return None

def repo_context(cwd):
    root = git(cwd, "rev-parse", "--show-toplevel")
    rootp = Path(root) if root else Path(cwd)
    return {
        "repository": rootp.name if root else None,
        "worktree": str(rootp) if root else None,
        "branch": git(rootp, "branch", "--show-current") if root else None,
        "commit_sha": git(rootp, "rev-parse", "HEAD") if root else None,
    }

def sanitize(value):
    if not isinstance(value, dict):
        return {}
    out = {}
    for key in ALLOWED_TOP:
        if key not in value or key in SENSITIVE_KEYS:
            continue
        v=value[key]
        if key == "usage" and isinstance(v, dict):
            out[key]={k:v[k] for k in ("input_tokens","output_tokens","cache_read_tokens","cache_write_tokens","requests","credits") if k in v and isinstance(v[k], (int,float))}
        elif isinstance(v, (str,int,float,bool)) or v is None:
            out[key]=v
    return out

def append_event(event, home=DEFAULT_HOME):
    day=datetime.now(timezone.utc).strftime("%Y-%m-%d")
    path=home/"events"/f"{day}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a",encoding="utf-8") as f:
        f.write(json.dumps(event,ensure_ascii=False,separators=(",",":"))+"\n")
    return path

def record(tool, raw, home=DEFAULT_HOME):
    safe=sanitize(raw)
    cwd=Path(safe.get("cwd") or os.getcwd())
    event={
        "schema_version":1,
        "event":{"id":str(uuid.uuid4()),"occurred_at":now(),"type":safe.get("hook_event_name") or safe.get("event_name") or "unknown"},
        "context":repo_context(cwd),
        "ai":{"tool":tool,"provider":"anthropic" if tool=="claude" else None,"model":{"name":safe.get("model") or safe.get("model_name"),"version":None}},
        "interaction":{"surface":"cli"},
        "execution":{"environment":"local","session_id":safe.get("session_id")},
        "usage":safe.get("usage",{}),
        "change":{"observed_file":safe.get("file_path")},
        "provenance":{"source":"agent_event","confidence":"confirmed" if safe.get("session_id") else "partial"},
    }
    append_event(event,home)
    return event

def main():
    p=argparse.ArgumentParser(description="Privacy-minimal Taviq provenance collector")
    sub=p.add_subparsers(dest="cmd",required=True)
    hook=sub.add_parser("hook"); hook.add_argument("--tool",required=True,choices=("claude","codex","kiro"))
    args=p.parse_args()
    if args.cmd=="hook":
        try: raw=json.load(sys.stdin)
        except Exception: raw={}
        event=record(args.tool,raw)
        print(json.dumps({"recorded":True,"event_id":event["event"]["id"]}))
if __name__=="__main__": main()
