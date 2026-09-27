#!/usr/bin/env python3
import argparse, json, os, urllib.request
from pathlib import Path

def post_envelope(url,token,path):
    data=path.read_bytes()
    req=urllib.request.Request(url.rstrip("/")+"/v1/envelopes",data=data,method="POST",headers={"Content-Type":"application/json","Authorization":"Bearer "+token})
    with urllib.request.urlopen(req,timeout=10) as r:
        return json.loads(r.read())

def main():
    p=argparse.ArgumentParser(); p.add_argument("--outbox",type=Path,required=True); p.add_argument("--relay",required=True); p.add_argument("--delete-after-ack",action="store_true")
    a=p.parse_args(); token=os.environ.get("TAVIQ_RELAY_TOKEN","")
    if not token: raise SystemExit("TAVIQ_RELAY_TOKEN is required")
    sent=0
    for path in sorted(a.outbox.glob("*.json")):
        result=post_envelope(a.relay,token,path)
        if result.get("accepted"):
            sent+=1
            if a.delete_after_ack: path.unlink()
    print(json.dumps({"sent":sent}))
if __name__=="__main__": main()
