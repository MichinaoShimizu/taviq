#!/usr/bin/env python3
import argparse, importlib.util, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("prov",ROOT/"src"/"taviq_provenance.py")
prov=importlib.util.module_from_spec(spec); spec.loader.exec_module(prov)
p=argparse.ArgumentParser()
p.add_argument("--session",type=Path,required=True)
p.add_argument("--output",type=Path,required=True)
p.add_argument("--hash-paths",action="store_true")
a=p.parse_args()
state=json.loads(a.session.read_text())
a.output.write_text(json.dumps(prov.build_envelope(state,a.hash_paths),ensure_ascii=False,indent=2))
