#!/usr/bin/env python3
"""Prepare a minimal Taviq commit trailer from environment metadata.

Designed to be called by a Git prepare-commit-msg hook or an agent integration.
It never adds unknown values and never adds usage/cost/content.
"""
import json, os, subprocess, sys
from pathlib import Path

ALLOWED_MODE={"assist","generate","agent","crew","mixed"}

def trailer_lines(env):
    tool=env.get("TAVIQ_TOOL")
    if not tool:
        return []
    lines=["Taviq-Provenance: v1",f"Taviq-Tool: {tool}"]
    mode=env.get("TAVIQ_MODE")
    if mode in ALLOWED_MODE: lines.append(f"Taviq-Mode: {mode}")
    model=env.get("TAVIQ_MODEL")
    if model: lines.append(f"Taviq-Model: {model}")
    return lines

def apply(path,env=os.environ):
    lines=trailer_lines(env)
    if not lines: return False
    p=Path(path); text=p.read_text()
    if "Taviq-Provenance:" in text: return False
    suffix="\n" if text.endswith("\n") else "\n\n"
    p.write_text(text+suffix+"\n".join(lines)+"\n")
    return True

if __name__=="__main__":
    if len(sys.argv)<2: raise SystemExit("commit message path required")
    apply(sys.argv[1])
