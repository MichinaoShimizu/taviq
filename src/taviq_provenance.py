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

def session_file(session_id, home=DEFAULT_HOME):
    key=hashlib.sha256((session_id or "unknown").encode()).hexdigest()[:24]
    return home/"sessions"/f"{key}.json"

def update_session(event, home=DEFAULT_HOME):
    sid=event.get("execution",{}).get("session_id")
    if not sid:
        return None
    path=session_file(sid,home); path.parent.mkdir(parents=True,exist_ok=True)
    state=json.loads(path.read_text()) if path.exists() else {"session_id":sid,"observed_files":[]}
    observed=event.get("change",{}).get("observed_file")
    if observed and observed not in state["observed_files"]:
        state["observed_files"].append(observed)
    state["repository"]=event.get("context",{}).get("repository")
    state["branch"]=event.get("context",{}).get("branch")
    state["commit_sha"]=event.get("context",{}).get("commit_sha")
    state["updated_at"]=event.get("event",{}).get("occurred_at")
    path.write_text(json.dumps(state,ensure_ascii=False,separators=(",",":")))
    return state

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

def build_envelope(session_state, hash_paths=False):
    paths=session_state.get("observed_files",[])
    if hash_paths:
        paths=[hashlib.sha256(p.encode()).hexdigest() for p in paths]
    return {
        "schema_version":1,
        "kind":"taviq-provenance-envelope",
        "session_ref":hashlib.sha256(session_state.get("session_id","unknown").encode()).hexdigest()[:24],
        "repository":session_state.get("repository"),
        "branch":session_state.get("branch"),
        "commit_sha":session_state.get("commit_sha"),
        "tool":session_state.get("tool"),
        "mode":session_state.get("mode"),
        "model":session_state.get("model"),
        "observed_files":paths,
        "path_encoding":"sha256" if hash_paths else "plain",
    }

def queue_envelope(session_state, home=DEFAULT_HOME, hash_paths=False):
    envelope=build_envelope(session_state,hash_paths=hash_paths)
    outbox=home/"outbox"
    outbox.mkdir(parents=True,exist_ok=True)
    path=outbox/f'{envelope["session_ref"]}.json'
    path.write_text(json.dumps(envelope,ensure_ascii=False,separators=(",",":")))
    return path

def list_outbox(home=DEFAULT_HOME):
    outbox=home/"outbox"
    return sorted(outbox.glob("*.json")) if outbox.exists() else []

def aggregate_coverage(changed_files, sessions):
    changed=set(changed_files or [])
    observed=set()
    tools=set()
    for state in sessions or []:
        observed.update(state.get("observed_files",[]))
        if state.get("tool"):
            tools.add(state["tool"])
    confirmed=changed & observed
    unknown=changed-confirmed
    coverage=(len(confirmed)/len(changed)*100) if changed else None
    return {
        "changed_files":len(changed),
        "confirmed_files":len(confirmed),
        "unknown_files":len(unknown),
        "coverage":coverage,
        "confirmed_paths":sorted(confirmed),
        "unknown_paths":sorted(unknown),
        "tools":sorted(tools),
    }

def github_check_summary(result):
    cov="n/a" if result["coverage"] is None else f'{result["coverage"]:.1f}%'
    return {
        "title":"Taviq AI Provenance",
        "summary":f'Coverage {cov} · confirmed {result["confirmed_files"]}/{result["changed_files"]} files · unknown {result["unknown_files"]}',
        "details":[
            "Coverage means provenance-confirmed changed files, not percentage of code written by AI.",
            "Unknown is not treated as human-only.",
        ],
    }

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
