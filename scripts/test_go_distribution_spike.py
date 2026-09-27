#!/usr/bin/env python3
import json, os, pathlib, shutil, subprocess, tempfile

ROOT=pathlib.Path(__file__).resolve().parents[1]
targets=[
    ("linux","amd64"),("linux","arm64"),
    ("darwin","amd64"),("darwin","arm64"),
    ("windows","amd64"),
]
results=[]
out=ROOT/".go-dist-spike"
shutil.rmtree(out,ignore_errors=True)
out.mkdir()

for goos,goarch in targets:
    suffix=".exe" if goos=="windows" else ""
    dest=out/f"taviq-{goos}-{goarch}{suffix}"
    env=dict(os.environ,GOOS=goos,GOARCH=goarch,CGO_ENABLED="0")
    subprocess.check_call(["go","build","-o",str(dest),"./cmd/taviq"],cwd=ROOT,env=env)
    results.append({"os":goos,"arch":goarch,"bytes":dest.stat().st_size})

linux=out/"taviq-linux-amd64"
with tempfile.TemporaryDirectory() as td:
    repo=pathlib.Path(td)/"external-repo"
    subprocess.check_call(["git","init",str(repo)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)

    # The external repository intentionally contains no Taviq source files.
    subprocess.check_call([str(linux),"init"],cwd=repo)

    msg=repo/"message"
    msg.write_text("External checkout test\n")
    env=dict(os.environ,TAVIQ_TOOL="claude",TAVIQ_MODE="agent")
    subprocess.check_call([str(linux),"hook","prepare-commit-msg",str(msg)],cwd=repo,env=env)
    text=msg.read_text()
    assert "Taviq-Provenance: v1" in text
    assert "Taviq-Tools: claude" in text

    doctor=subprocess.run([str(linux),"doctor"],cwd=repo,text=True,capture_output=True)
    assert doctor.returncode==0,doctor.stderr+doctor.stdout

    subprocess.check_call([str(linux),"deinit"],cwd=repo)

shutil.rmtree(out)
print(json.dumps({"targets":results,"binary_only_external_repo":"passed"},indent=2))
