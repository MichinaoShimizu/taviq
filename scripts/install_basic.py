#!/usr/bin/env python3
import argparse, os, subprocess, sys
from pathlib import Path

HOOK='''#!/bin/sh
python3 "$(git rev-parse --show-toplevel)/scripts/taviq_prepare_commit_msg.py" "$1"
'''

def main():
    p=argparse.ArgumentParser(); p.add_argument("--repo",type=Path,default=Path("."))
    a=p.parse_args(); root=Path(subprocess.check_output(["git","-C",str(a.repo),"rev-parse","--show-toplevel"],text=True).strip())
    hooks=root/".taviq"/"hooks"; hooks.mkdir(parents=True,exist_ok=True)
    target=hooks/"prepare-commit-msg"; target.write_text(HOOK); target.chmod(0o755)
    subprocess.check_call(["git","-C",str(root),"config","core.hooksPath",".taviq/hooks"])
    print("Taviq Basic hook installed. Set TAVIQ_TOOL and optional TAVIQ_MODE/TAVIQ_MODEL in the AI execution environment.")
if __name__=="__main__": main()
