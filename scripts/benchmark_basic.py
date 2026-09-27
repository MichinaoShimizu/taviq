#!/usr/bin/env python3
import importlib.util, json, statistics, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("hook",ROOT/"scripts"/"taviq_prepare_commit_msg.py")
hook=importlib.util.module_from_spec(spec); spec.loader.exec_module(hook)

def main():
    samples=[]
    sizes=[]
    for _ in range(100):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"msg"; p.write_text("Test commit\n")
            r=hook.apply(p,{"TAVIQ_TOOL":"claude","TAVIQ_MODE":"agent"})
            samples.append(r["elapsed_ms"]); sizes.append(r["metadata_bytes"])
    result={
        "runs":len(samples),
        "median_ms":statistics.median(samples),
        "p95_ms":sorted(samples)[int(len(samples)*0.95)-1],
        "max_ms":max(samples),
        "metadata_bytes":max(sizes),
        "targets":{"hook_ms_lt":50,"metadata_bytes_lt":1024},
        "passes":{"hook_median":statistics.median(samples)<50,"metadata_size":max(sizes)<1024},
        "ai_calls":0,
        "ai_tokens":0,
        "ai_credits":0,
    }
    print(json.dumps(result,indent=2))
if __name__=="__main__": main()
