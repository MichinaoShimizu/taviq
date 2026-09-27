#!/usr/bin/env python3
"""Build a GitHub-integration-ready provenance report from explicit inputs."""
import argparse, importlib.util, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("prov",ROOT/"src"/"taviq_provenance.py")
prov=importlib.util.module_from_spec(spec); spec.loader.exec_module(prov)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--changed-files",type=Path,required=True,help="JSON array of PR changed file paths supplied by GitHub integration")
    p.add_argument("--sessions",type=Path,required=True,help="JSON array of normalized Taviq session states")
    p.add_argument("--output",type=Path)
    a=p.parse_args()
    changed=json.loads(a.changed_files.read_text())
    sessions=json.loads(a.sessions.read_text())
    result=prov.aggregate_coverage(changed,sessions)
    out={"provenance":result,"check":prov.github_check_summary(result)}
    payload=json.dumps(out,ensure_ascii=False,indent=2)
    if a.output: a.output.write_text(payload)
    else: print(payload)
if __name__=="__main__": main()
