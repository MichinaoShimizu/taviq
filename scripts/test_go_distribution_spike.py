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
    home = pathlib.Path(td) / "home"
    config = pathlib.Path(td) / "config"
    home.mkdir()
    (home / ".claude").mkdir()
    subprocess.check_call(["git", "init", str(repo)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    env_machine = dict(os.environ, XDG_CONFIG_HOME=str(config), HOME=str(home))
    env_machine.pop("CLAUDE_CONFIG_DIR", None)
    subprocess.check_call([str(linux), "install"], cwd=repo, env=env_machine)
    subprocess.check_call([str(linux), "init"], cwd=repo, env=env_machine)

    assert (repo / ".taviq.yml").read_text() == "version: 1\n"
    assert not (repo / ".taviq" / "hooks" / "prepare-commit-msg").exists()

    msg = repo / "message"
    msg.write_text("External checkout test\n")
    env_hook = dict(env_machine, TAVIQ_TOOL="claude", TAVIQ_MODE="agent")
    subprocess.check_call([str(linux), "hook", "prepare-commit-msg", str(msg)], cwd=repo, env=env_hook)
    text = msg.read_text()
    assert "Taviq-Provenance: v1" in text
    assert "Taviq-Tools: claude" in text

    claude_settings = json.loads((home / ".claude" / "settings.json").read_text())
    assert "hook claude-code" in json.dumps(claude_settings["hooks"]["PreToolUse"])
    claude_msg = repo / "claude-message"
    claude_msg.write_text("Claude hook test\n")
    event = json.dumps({"cwd": str(repo), "hook_event_name": "PreToolUse", "tool_name": "Write"})
    claude_hook = subprocess.run([str(linux), "hook", "claude-code"], cwd=home, env=env_machine, input=event, text=True, capture_output=True)
    assert claude_hook.returncode == 0 and claude_hook.stdout == "" and claude_hook.stderr == "", claude_hook
    subprocess.check_call([str(linux), "hook", "prepare-commit-msg", str(claude_msg)], cwd=repo, env=env_machine)
    assert "Taviq-Tools: claude" in claude_msg.read_text()

    doctor = subprocess.run([str(linux), "doctor"], cwd=repo, env=env_machine, text=True, capture_output=True)
    assert doctor.returncode == 0, doctor.stderr + doctor.stdout

    subprocess.check_call([str(linux), "deinit"], cwd=repo, env=env_machine)
    subprocess.check_call([str(linux), "uninstall"], cwd=repo, env=env_machine)
    assert json.loads((home / ".claude" / "settings.json").read_text()) == {}

shutil.rmtree(out)
print(json.dumps({"targets": results, "binary_only_external_repo": "passed"}, indent=2))
