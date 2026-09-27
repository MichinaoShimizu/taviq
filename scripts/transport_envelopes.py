#!/usr/bin/env python3
"""Transport queued Taviq envelopes without coupling the collector to a vendor."""
import argparse, json, shutil
from pathlib import Path

def copy_transport(outbox: Path, destination: Path):
    destination.mkdir(parents=True,exist_ok=True)
    moved=[]
    for src in sorted(outbox.glob("*.json")):
        payload=json.loads(src.read_text())
        if payload.get("kind")!="taviq-provenance-envelope":
            continue
        dst=destination/src.name
        shutil.copy2(src,dst)
        moved.append(str(dst))
    return moved

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--outbox",type=Path,required=True)
    p.add_argument("--transport",choices=("directory",),default="directory")
    p.add_argument("--destination",type=Path,required=True)
    a=p.parse_args()
    moved=copy_transport(a.outbox,a.destination)
    print(json.dumps({"transport":a.transport,"exported":len(moved),"files":moved}))
if __name__=="__main__": main()
