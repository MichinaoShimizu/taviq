#!/usr/bin/env python3
from __future__ import annotations
import argparse, hmac, json, os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

MAX_BODY=64*1024
ALLOWED={"schema_version","kind","session_ref","repository","branch","commit_sha","tool","mode","model","observed_files","path_encoding"}

def validate_envelope(x):
    if not isinstance(x,dict) or x.get("kind")!="taviq-provenance-envelope":
        return False,"invalid envelope kind"
    if set(x)-ALLOWED:
        return False,"unexpected fields"
    if not isinstance(x.get("session_ref"),str):
        return False,"missing session_ref"
    if not isinstance(x.get("observed_files",[]),list):
        return False,"invalid observed_files"
    return True,None

def store_envelope(root,x):
    repo=(x.get("repository") or "unknown").replace("/","_")
    commit=x.get("commit_sha") or "unknown"
    d=root/repo/commit; d.mkdir(parents=True,exist_ok=True)
    p=d/f'{x["session_ref"]}.json'
    p.write_text(json.dumps(x,ensure_ascii=False,separators=(",",":")))
    return p

def load_commit(root,repo,commit):
    d=root/repo.replace("/","_")/commit
    if not d.exists(): return []
    return [json.loads(p.read_text()) for p in sorted(d.glob("*.json"))]

class Handler(BaseHTTPRequestHandler):
    store=Path(".taviq-relay")
    token=""
    def sendj(self,status,obj):
        body=json.dumps(obj,ensure_ascii=False).encode()
        self.send_response(status); self.send_header("Content-Type","application/json"); self.send_header("Content-Length",str(len(body))); self.end_headers(); self.wfile.write(body)
    def auth(self):
        h=self.headers.get("Authorization","")
        return bool(self.token) and h.startswith("Bearer ") and hmac.compare_digest(h[7:],self.token)
    def do_POST(self):
        if self.path!="/v1/envelopes": return self.sendj(404,{"error":"not found"})
        if not self.auth(): return self.sendj(401,{"error":"unauthorized"})
        try: n=int(self.headers.get("Content-Length","0"))
        except ValueError: n=0
        if n<=0 or n>MAX_BODY: return self.sendj(413,{"error":"invalid body size"})
        try: x=json.loads(self.rfile.read(n))
        except Exception: return self.sendj(400,{"error":"invalid json"})
        ok,err=validate_envelope(x)
        if not ok: return self.sendj(400,{"error":err})
        store_envelope(self.store,x)
        return self.sendj(202,{"accepted":True,"session_ref":x["session_ref"]})
    def do_GET(self):
        if not self.auth(): return self.sendj(401,{"error":"unauthorized"})
        u=urlparse(self.path)
        if u.path!="/v1/envelopes": return self.sendj(404,{"error":"not found"})
        q=parse_qs(u.query); repo=q.get("repository",[None])[0]; commit=q.get("commit_sha",[None])[0]
        if not repo or not commit: return self.sendj(400,{"error":"repository and commit_sha required"})
        return self.sendj(200,{"envelopes":load_commit(self.store,repo,commit)})
    def log_message(self,fmt,*args): pass

def main():
    p=argparse.ArgumentParser(); p.add_argument("--host",default="127.0.0.1"); p.add_argument("--port",type=int,default=8787); p.add_argument("--store",type=Path,default=Path(".taviq-relay"))
    a=p.parse_args(); token=os.environ.get("TAVIQ_RELAY_TOKEN","")
    if not token: raise SystemExit("TAVIQ_RELAY_TOKEN is required")
    Handler.store=a.store; Handler.token=token
    ThreadingHTTPServer((a.host,a.port),Handler).serve_forever()
if __name__=="__main__": main()
