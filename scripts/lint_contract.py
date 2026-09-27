#!/usr/bin/env python3
"""Repository contract lint for Taviq Basic. Standard library only."""
import re, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
TEXT_EXT={".md",".py",".yml",".yaml",".json"}
errors=[]

def fail(path,msg):
    errors.append(f"{path}: {msg}")

def text_files():
    for p in ROOT.rglob("*"):
        if p.is_file() and p.suffix in TEXT_EXT and ".git" not in p.parts:
            yield p

for p in text_files():
    try: s=p.read_text()
    except UnicodeDecodeError: continue
    rel=p.relative_to(ROOT)

    if "\\n" in s:
        fail(rel,'contains literal \\n; likely escaped-newline corruption')

    if p.suffix==".md":
        for target in re.findall(r"\[[^]]+\]\(([^)]+)\)",s):
            if target.startswith(("http://","https://","#","mailto:")): continue
            target=target.split("#",1)[0]
            if target and not (p.parent/target).resolve().exists():
                fail(rel,f"broken relative Markdown link: {target}")

# Normative terminology.
readme=(ROOT/"README.md").read_text()
schema=(ROOT/"docs/provenance-schema.md").read_text()
trust=(ROOT/"docs/verified-provenance.md").read_text()

for path,s in [(Path("README.md"),readme),(Path("docs/provenance-schema.md"),schema),(Path("docs/verified-provenance.md"),trust)]:
    if re.search(r"\bconfirmed\b",s,re.I):
        fail(path,"uses legacy Confirmed terminology; use Recorded/Unknown")

if "Unknown does not mean Human-only" not in schema:
    fail(Path("docs/provenance-schema.md"),"must explicitly preserve Unknown != Human-only")

if "Recorded does not mean cryptographically verified" not in schema:
    fail(Path("docs/provenance-schema.md"),"must preserve Recorded != cryptographically verified")

# Basic provenance privacy boundary: reject forbidden durable trailer field names.
hook=(ROOT/"scripts/taviq_prepare_commit_msg.py").read_text()
for forbidden in ["Prompt","Response","Token","Credit","Cost","Developer","Identity","Source","Diff"]:
    if re.search(rf"Taviq-{forbidden}\s*:",hook,re.I):
        fail(Path("scripts/taviq_prepare_commit_msg.py"),f"forbidden Basic trailer field: Taviq-{forbidden}")

# Basic should remain zero-secret and zero-network by default.
for p in [ROOT/"scripts/taviq_prepare_commit_msg.py",ROOT/"scripts/set_runtime.py"]:
    s=p.read_text()
    for marker in ["TAVIQ_SIGNING_KEY","requests.","urllib.request","http://","https://"]:
        if marker in s:
            fail(p.relative_to(ROOT),f"Basic local path introduces secret/network marker: {marker}")

if errors:
    print("Taviq contract lint failed:")
    for e in errors: print(" -",e)
    raise SystemExit(1)
print("Taviq contract lint passed.")
