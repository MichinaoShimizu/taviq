#!/usr/bin/env python3
"""Build versioned Taviq release binaries with SHA-256 checksums. Standard library only."""
import hashlib
import os
import pathlib
import platform
import re
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
TARGETS = [
    ("linux", "amd64"),
    ("linux", "arm64"),
    ("darwin", "amd64"),
    ("darwin", "arm64"),
    ("windows", "amd64"),
]

if len(sys.argv) not in (2, 3):
    raise SystemExit("usage: build_release.py <version> [out-dir]")
version = sys.argv[1]
if not re.fullmatch(r"v\d+\.\d+\.\d+(-[0-9A-Za-z.-]+)?", version):
    raise SystemExit(f"version must look like v0.1.0 or v0.1.0-rc.1: {version}")
out = pathlib.Path(sys.argv[2]) if len(sys.argv) == 3 else ROOT / "dist"
shutil.rmtree(out, ignore_errors=True)
out.mkdir(parents=True)

sums = []
for goos, goarch in TARGETS:
    suffix = ".exe" if goos == "windows" else ""
    name = f"taviq-{version}-{goos}-{goarch}{suffix}"
    env = dict(os.environ, GOOS=goos, GOARCH=goarch, CGO_ENABLED="0")
    subprocess.check_call(
        ["go", "build", "-trimpath", "-ldflags", f"-s -w -X main.version={version}", "-o", str(out / name), "./cmd/taviq"],
        cwd=ROOT,
        env=env,
    )
    sums.append(f"{hashlib.sha256((out / name).read_bytes()).hexdigest()}  {name}")

(out / "SHA256SUMS").write_text("\n".join(sums) + "\n")

# The host binary must report exactly the stamped version.
host = {"x86_64": "amd64", "amd64": "amd64", "aarch64": "arm64", "arm64": "arm64"}.get(platform.machine().lower())
host_os = {"Linux": "linux", "Darwin": "darwin"}.get(platform.system())
if host and host_os:
    reported = subprocess.check_output([str(out / f"taviq-{version}-{host_os}-{host}"), "version"], text=True).strip()
    if reported != f"taviq {version}":
        raise SystemExit(f"host binary reports {reported!r}, want 'taviq {version}'")

print((out / "SHA256SUMS").read_text(), end="")
