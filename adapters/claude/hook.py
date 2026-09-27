#!/usr/bin/env python3
"""Claude Code hook adapter.

Reads the hook JSON from stdin and forwards only allow-listed metadata to
Taviq's local collector. The collector deliberately ignores prompt/response,
tool input/output, diffs and source-code content.
"""
from pathlib import Path
import subprocess, sys

root=Path(__file__).resolve().parents[2]
raise SystemExit(subprocess.call([sys.executable,str(root/"src"/"taviq_provenance.py"),"hook","--tool","claude"],stdin=sys.stdin))
