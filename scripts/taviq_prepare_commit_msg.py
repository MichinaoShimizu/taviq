#!/usr/bin/env python3
"""Prepare a minimal Taviq commit trailer from environment metadata.

Designed to be called by a Git prepare-commit-msg hook or an agent integration.
It never adds unknown values and never adds usage/cost/content.
"""
import hashlib, hmac, json, os, subprocess, sys, time
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

def provenance_signature(tool,mode,model,env):
    key=env.get("TAVIQ_SIGNING_KEY")
    repo=env.get("TAVIQ_REPOSITORY")
    ref=env.get("TAVIQ_PROVENANCE_REF")
    if not key or not repo or not ref:
        return None
    payload={"version":"v1","tool":tool or "","mode":mode or "","model":model or "","repository":repo,"ref":ref}
    canonical="\\n".join(f"{k}={payload[k]}" for k in ("version","tool","mode","model","repository","ref")).encode()
    return hmac.new(key.encode(),canonical,hashlib.sha256).hexdigest()

def apply(path,env=os.environ):
    lines=trailer_lines(env)
    if not lines: return {"applied":False,"elapsed_ms":(time.perf_counter()-started)*1000,"metadata_bytes":0}
    p=Path(path); text=p.read_text()
    if "Taviq-Provenance:" in text: return {"applied":False,"elapsed_ms":(time.perf_counter()-started)*1000,"metadata_bytes":0}
    suffix="\n" if text.endswith("\n") else "\n\n"
    p.write_text(text+suffix+"\n".join(lines)+"\n")
    return True

if __name__=="__main__":
    if len(sys.argv)<2: raise SystemExit("commit message path required")
    apply(sys.argv[1])
