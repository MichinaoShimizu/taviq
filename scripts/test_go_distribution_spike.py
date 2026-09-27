#!/usr/bin/env python3
import json
import os
import pathlib
import shutil
import subprocess
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
targets = [
    ("linux", "amd64"),
    ("linux", "arm64"),
    ("darwin", "amd64"),
    ("darwin", "arm64"),
    ("windows", "amd64"),
]
results = []
out = ROOT / ".go-dist-spike"
shutil.rmtree(out, ignore_errors=True)
out.mkdir()

for goos, goarch in targets:
    suffix = ".exe" if goos == "windows" else ""
    dest = out / f"taviq-{goos}-{goarch}{suffix}"
    env = dict(os.environ, GOOS=goos, GOARCH=goarch, CGO_ENABLED="0")
    subprocess.check_call(["go", "build", "-o", str(dest), "./cmd/taviq"], cwd=ROOT, env=env)
    results.append({"os": goos, "arch": goarch, "bytes": dest.stat().st_size})

linux = out / "taviq-linux-amd64"
with tempfile.TemporaryDirectory() as td:
    repo = pathlib.Path(td) / "external-repo"
    subprocess.check_call(["git", "init", str(repo)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # The external repository intentionally contains no Taviq source files.
    (repo / ".taviq.yml").write_text("version: 1\n")
    env_machine = dict(os.environ, XDG_CONFIG_HOME=str(pathlib.Path(td) / "config"), HOME=str(pathlib.Path(td) / "home"))\n    pathlib.Path(env_machine["HOME"]).mkdir()\n    subprocess.check_call([str(linux), "install"], cwd=repo, env=env_machine)\n    subprocess.check_call([str(linux), "init"], cwd=repo, env=env_machine)

    msg = repo / "message"
    msg.write_text("External checkout test\n")
    env = dict(os.environ, TAVIQ_TOOL="claude", TAVIQ_MODE="agent")
    env.update({"XDG_CONFIG_HOME": env_machine["XDG_CONFIG_HOME"], "HOME": env_machine["HOME"]})\n    subprocess.check_call([str(linux), "hook", "prepare-commit-msg", str(msg)], cwd=repo, env=env)
    text = msg.read_text()
    assert "Taviq-Provenance: v1" in text
    assert "Taviq-Tools: claude" in text

    doctor = subprocess.run([str(linux), "doctor"], cwd=repo, env=env_machine, text=True, capture_output=True)
    assert doctor.returncode == 0, doctor.stderr + doctor.stdout

    subprocess.check_call([str(linux), "deinit"], cwd=repo, env=env_machine)\n    subprocess.check_call([str(linux), "uninstall"], cwd=repo, env=env_machine)

shutil.rmtree(out)
print(json.dumps({"targets": results, "binary_only_external_repo": "passed"}, indent=2))
