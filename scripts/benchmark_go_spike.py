#!/usr/bin/env python3
import json, os, pathlib, statistics, subprocess, tempfile, time

root=pathlib.Path(__file__).resolve().parents[1]
binary=root/".tmp-taviq-go"
subprocess.check_call(["go","build","-o",str(binary),"./cmd/taviq"],cwd=root)
size=binary.stat().st_size
samples=[]
with tempfile.TemporaryDirectory() as d:
    repo=pathlib.Path(d)
    subprocess.check_call(["git","init",str(repo)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    env=dict(os.environ);env["TAVIQ_TOOL"]="claude";env["TAVIQ_MODE"]="agent"
    for i in range(20):
        msg=repo/f"msg-{i}";msg.write_text("Change\n")
        start=time.perf_counter()
        subprocess.check_call([str(binary),"hook","prepare-commit-msg",str(msg)],cwd=repo,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        samples.append((time.perf_counter()-start)*1000)
binary.unlink()
print(json.dumps({
    "binary_bytes":size,
    "hook_ms_median":statistics.median(samples),
    "hook_ms_p95":sorted(samples)[int(len(samples)*0.95)-1],
    "samples":len(samples)
},indent=2))
