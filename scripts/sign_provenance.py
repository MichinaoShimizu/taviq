#!/usr/bin/env python3
import argparse, hashlib, hmac, json, os

FIELDS=("version","tool","mode","model","repository","ref")

def canonical(x):
    return "\n".join(f"{k}={x.get(k,'')}" for k in FIELDS).encode()

def sign(x,key):
    return hmac.new(key.encode(),canonical(x),hashlib.sha256).hexdigest()

def verify(x,key,signature):
    return hmac.compare_digest(sign(x,key),signature)

def main():
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest="cmd",required=True)
    for name in ("sign","verify"):
        q=sub.add_parser(name); q.add_argument("--payload",required=True); q.add_argument("--signature")
    a=p.parse_args(); key=os.environ.get("TAVIQ_SIGNING_KEY")
    if not key: raise SystemExit("TAVIQ_SIGNING_KEY is required")
    x=json.loads(a.payload)
    if a.cmd=="sign": print(sign(x,key))
    else: raise SystemExit(0 if a.signature and verify(x,key,a.signature) else 1)
if __name__=="__main__": main()
