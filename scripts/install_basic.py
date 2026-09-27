#!/usr/bin/env python3
import argparse
import subprocess
from pathlib import Path

HOOK = '''#!/bin/sh
if command -v taviq >/dev/null 2>&1; then
  exec taviq hook prepare-commit-msg "$1"
fi
exec python3 "$(git rev-parse --show-toplevel)/scripts/taviq_prepare_commit_msg.py" "$1"
'''

def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()

def repo_root(repo):
    return Path(git(repo, "rev-parse", "--show-toplevel"))

def install(root):
    hooks = root / ".taviq" / "hooks"
    hooks.mkdir(parents=True, exist_ok=True)
    target = hooks / "prepare-commit-msg"
    probe = subprocess.run(["git", "-C", str(root), "config", "--get", "core.hooksPath"], capture_output=True, text=True)
    previous = probe.stdout.strip() if probe.returncode == 0 else ""
    state = root / ".taviq" / "install-state"
    if not state.exists():
        state.write_text(previous)
    target.write_text(HOOK)
    target.chmod(0o755)
    subprocess.check_call(["git", "-C", str(root), "config", "core.hooksPath", ".taviq/hooks"])
    print("Taviq Basic installed. Tool integrations will record provenance automatically.")

def uninstall(root):
    state = root / ".taviq" / "install-state"
    previous = state.read_text() if state.exists() else ""
    if previous:
        subprocess.check_call(["git", "-C", str(root), "config", "core.hooksPath", previous])
    else:
        subprocess.run(["git", "-C", str(root), "config", "--unset", "core.hooksPath"], check=False)
    for path in [root / ".taviq" / "hooks" / "prepare-commit-msg", root / ".taviq" / "runtime.json", state]:
        if path.exists():
            path.unlink()
    print("Taviq Basic uninstalled. Previous core.hooksPath restored when available.")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", nargs="?", choices=["install", "uninstall"], default="install")
    parser.add_argument("--repo", type=Path, default=Path("."))
    args = parser.parse_args()
    root = repo_root(args.repo)
    install(root) if args.command == "install" else uninstall(root)

if __name__ == "__main__":
    main()
