#!/usr/bin/env python3
"""Diagnose Taviq Basic repository readiness without changing state."""
import argparse, json, subprocess
from pathlib import Path

def git(root,*args):
    r=subprocess.run(["git","-C",str(root),*args],text=True,capture_output=True)
    return r.returncode,r.stdout.strip()

def repo_root(path):
    code,out=git(path,"rev-parse","--show-toplevel")
    if code: raise SystemExit("not a Git repository")
    return Path(out)

def diagnose(root):
    code,hooks=git(root,"config","--get","core.hooksPath")
    expected=".taviq/hooks"
    checks={
        "git_repository":True,
        "hooks_path": code==0 and hooks==expected,
        "prepare_commit_msg_hook":(root/".taviq/hooks/prepare-commit-msg").exists(),
        "runtime_writer":(root/"scripts/set_runtime.py").exists(),
        "commit_writer":(root/"scripts/taviq_prepare_commit_msg.py").exists(),
        "schema":(root/"docs/provenance-schema.md").exists(),
        "claude_integration":(root/".claude/settings.json").exists(),
        "codex_integration":(root/".codex/plugins/taviq-basic/hooks.json").exists(),
        "kiro_integration":(root/".kiro/hooks/taviq.json").exists(),
        "github_pr_summary":(root/".github/workflows/taviq-basic.yml").exists(),
    }
    core=("hooks_path","prepare_commit_msg_hook","runtime_writer","commit_writer")
    return {
        "status":"ready" if all(checks[k] for k in core) else "incomplete",
        "core_ready":all(checks[k] for k in core),
        "checks":checks,
        "optional":{"github_pr_summary":checks["github_pr_summary"]},
    }

def main():
    p=argparse.ArgumentParser(); p.add_argument("--repo",type=Path,default=Path(".")); p.add_argument("--json",action="store_true"); a=p.parse_args()
    result=diagnose(repo_root(a.repo))
    if a.json:
        print(json.dumps(result,indent=2))
    else:
        print("Taviq Doctor:",result["status"])
        for name,ok in result["checks"].items(): print(("✓" if ok else "✗"),name)
        print("Core provenance:", "ready" if result["core_ready"] else "incomplete")
        print("GitHub PR summary:", "enabled" if result["optional"]["github_pr_summary"] else "optional/not installed")
    raise SystemExit(0 if result["core_ready"] else 1)

if __name__=="__main__": main()
