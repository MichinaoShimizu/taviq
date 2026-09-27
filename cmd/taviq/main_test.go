package main

import (
	"encoding/json"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"
)

func enterRepo(t *testing.T) string {
	t.Helper()
	dir := t.TempDir()
	if err := exec.Command("git", "init", dir).Run(); err != nil {
		t.Fatal(err)
	}
	old, _ := os.Getwd()
	t.Cleanup(func() { _ = os.Chdir(old) })
	if err := os.Chdir(dir); err != nil {
		t.Fatal(err)
	}
	return dir
}

func configureGit() {
	_ = exec.Command("git", "config", "user.email", "test@example.com").Run()
	_ = exec.Command("git", "config", "user.name", "Taviq Test").Run()
}

func TestHookGoldenTrailer(t *testing.T) {
	dir := enterRepo(t)
	if err := initMarker(); err != nil {
		t.Fatal(err)
	}
	msg := filepath.Join(dir, "msg")
	_ = os.WriteFile(msg, []byte("Change\n"), 0o644)
	t.Setenv("TAVIQ_TOOL", "claude")
	t.Setenv("TAVIQ_MODE", "agent")
	if err := hook(msg); err != nil {
		t.Fatal(err)
	}
	b, _ := os.ReadFile(msg)
	want := "Change\n\nTaviq-Provenance: v1\nTaviq-Tools: claude\nTaviq-Modes: agent\n"
	if string(b) != want {
		t.Fatalf("golden mismatch\nwant=%q\ngot =%q", want, string(b))
	}
}

func TestHookMultiValueSorted(t *testing.T) {
	dir := enterRepo(t)
	if err := initMarker(); err != nil {
		t.Fatal(err)
	}
	path, err := runtimePath()
	if err != nil {
		t.Fatal(err)
	}
	_ = os.MkdirAll(filepath.Dir(path), 0o755)
	_ = os.WriteFile(path, []byte(`{"tools":["codex","claude"],"modes":["agent"],"models":["z","a"]}`), 0o644)
	msg := filepath.Join(dir, "msg")
	_ = os.WriteFile(msg, []byte("X\n"), 0o644)
	if err := hook(msg); err != nil {
		t.Fatal(err)
	}
	b, _ := os.ReadFile(msg)
	for _, want := range []string{"Taviq-Tools: claude,codex", "Taviq-Modes: agent", "Taviq-Models: a,z"} {
		if !strings.Contains(string(b), want) {
			t.Fatalf("missing %s", want)
		}
	}
}

func TestObserveAccumulatesAndResetsOnHeadChange(t *testing.T) {
	enterRepo(t)
	configureGit()
	if err := initMarker(); err != nil {
		t.Fatal(err)
	}
	path, err := runtimePath()
	if err != nil {
		t.Fatal(err)
	}
	_ = os.WriteFile("a", []byte("a"), 0o644)
	_ = exec.Command("git", "add", "a").Run()
	_ = exec.Command("git", "commit", "-m", "a").Run()

	_ = observe("claude", "agent", "sonnet")
	_ = observe("codex", "agent", "gpt-x")
	_ = observe("claude", "agent", "sonnet")
	b, _ := os.ReadFile(path)
	var x Runtime
	_ = json.Unmarshal(b, &x)
	if strings.Join(x.Tools, ",") != "claude,codex" || strings.Join(x.Models, ",") != "gpt-x,sonnet" {
		t.Fatalf("unexpected runtime: %+v", x)
	}
	oldHead := x.BaseHead

	_ = os.WriteFile("b", []byte("b"), 0o644)
	_ = exec.Command("git", "add", "b").Run()
	_ = exec.Command("git", "commit", "-m", "b").Run()
	_ = observe("kiro", "crew", "")
	b, _ = os.ReadFile(path)
	_ = json.Unmarshal(b, &x)
	if x.BaseHead == oldHead || strings.Join(x.Tools, ",") != "kiro" || strings.Join(x.Modes, ",") != "crew" {
		t.Fatalf("expected new HEAD window: %+v", x)
	}
}

func TestObserveThenHookEndToEnd(t *testing.T) {
	dir := enterRepo(t)
	if err := initMarker(); err != nil {
		t.Fatal(err)
	}
	_ = observe("claude", "agent", "sonnet")
	_ = observe("codex", "agent", "gpt-x")
	msg := filepath.Join(dir, "msg")
	_ = os.WriteFile(msg, []byte("Change\n"), 0o644)
	if err := hook(msg); err != nil {
		t.Fatal(err)
	}
	b, _ := os.ReadFile(msg)
	for _, want := range []string{
		"Taviq-Provenance: v1",
		"Taviq-Tools: claude,codex",
		"Taviq-Modes: agent",
		"Taviq-Models: gpt-x,sonnet",
	} {
		if !strings.Contains(string(b), want) {
			t.Fatalf("missing %s", want)
		}
	}
}

func TestMachineInstallUninstallIsIdempotent(t *testing.T) {
	config := t.TempDir()
	home := t.TempDir()
	t.Setenv("XDG_CONFIG_HOME", config)
	t.Setenv("HOME", home)
	t.Setenv("CLAUDE_CONFIG_DIR", "")
	t.Setenv("CODEX_HOME", "")

	if err := machineInstall(); err != nil {
		t.Fatal(err)
	}
	if err := machineInstall(); err != nil {
		t.Fatal(err)
	}

	dir, err := machineConfigDir()
	if err != nil {
		t.Fatal(err)
	}
	b, err := os.ReadFile(filepath.Join(dir, "state.json"))
	if err != nil {
		t.Fatal(err)
	}
	var state MachineState
	if err := json.Unmarshal(b, &state); err != nil {
		t.Fatal(err)
	}
	if state.SchemaVersion != 1 || !state.Installed {
		t.Fatalf("unexpected machine state: %+v", state)
	}

	if err := machineUninstall(); err != nil {
		t.Fatal(err)
	}
	if err := machineUninstall(); err != nil && !os.IsNotExist(err) {
		t.Fatal(err)
	}
	if _, err := os.Stat(dir); !os.IsNotExist(err) {
		t.Fatal("expected Taviq config directory removed")
	}
}

func TestRepositoryMarkerLifecycle(t *testing.T) {
	dir := enterRepo(t)
	enabled, err := repoEnabled()
	if err != nil || enabled {
		t.Fatalf("expected disabled repo: %v %v", enabled, err)
	}
	if err := initMarker(); err != nil {
		t.Fatal(err)
	}
	if err := initMarker(); err != nil {
		t.Fatal(err)
	}
	enabled, err = repoEnabled()
	if err != nil || !enabled {
		t.Fatalf("expected enabled repo: %v %v", enabled, err)
	}
	b, _ := os.ReadFile(filepath.Join(dir, repoMarker))
	if string(b) != "version: 1\n" {
		t.Fatalf("unexpected marker: %q", b)
	}
	if err := deinitMarker(); err != nil {
		t.Fatal(err)
	}
	enabled, err = repoEnabled()
	if err != nil || enabled {
		t.Fatalf("expected disabled repo after deinit: %v %v", enabled, err)
	}
}

func TestRepositoryMarkerFailsClosedOnUnknownVersion(t *testing.T) {
	dir := enterRepo(t)
	_ = os.WriteFile(filepath.Join(dir, repoMarker), []byte("version: 2\n"), 0o644)
	enabled, err := repoEnabled()
	if err != nil {
		t.Fatal(err)
	}
	if enabled {
		t.Fatal("unknown marker version must not enable repository")
	}
}

func TestHookIgnoresRepositoryWithoutMarker(t *testing.T) {
	dir := enterRepo(t)
	msg := filepath.Join(dir, "msg")
	_ = os.WriteFile(msg, []byte("Change\n"), 0o644)
	t.Setenv("TAVIQ_TOOL", "claude")
	if err := hook(msg); err != nil {
		t.Fatal(err)
	}
	b, _ := os.ReadFile(msg)
	if string(b) != "Change\n" {
		t.Fatalf("unmarked repository must be untouched: %q", b)
	}
}

func TestGlobalGitHookRefusesExistingOwner(t *testing.T) {
	config := t.TempDir()
	home := t.TempDir()
	t.Setenv("XDG_CONFIG_HOME", config)
	t.Setenv("HOME", home)
	t.Setenv("CLAUDE_CONFIG_DIR", "")
	t.Setenv("CODEX_HOME", "")
	_ = exec.Command("git", "config", "--global", "core.hooksPath", "/other/hooks").Run()
	err := installGlobalGitHook()
	if err == nil {
		t.Fatal("expected existing global hooksPath conflict")
	}
	out, _ := exec.Command("git", "config", "--global", "--get", "core.hooksPath").Output()
	if strings.TrimSpace(string(out)) != "/other/hooks" {
		t.Fatal("existing global hooksPath must remain unchanged")
	}
}

func TestMarkerOnlyInitCreatesNoRepositoryHook(t *testing.T) {
	dir := enterRepo(t)
	if err := initMarker(); err != nil {
		t.Fatal(err)
	}
	if _, err := os.Stat(filepath.Join(dir, ".taviq", "hooks", "prepare-commit-msg")); !os.IsNotExist(err) {
		t.Fatal("repository-local hook must not be created")
	}
}

func TestDoctorUsesMachineHookAndMarker(t *testing.T) {
	config := t.TempDir()
	home := t.TempDir()
	t.Setenv("XDG_CONFIG_HOME", config)
	t.Setenv("HOME", home)
	t.Setenv("CLAUDE_CONFIG_DIR", "")
	t.Setenv("CODEX_HOME", "")
	enterRepo(t)
	if err := initMarker(); err != nil {
		t.Fatal(err)
	}
	if err := machineInstall(); err != nil {
		t.Fatal(err)
	}
	x, err := diagnose()
	if err != nil {
		t.Fatal(err)
	}
	if !x["core_ready"].(bool) {
		t.Fatalf("expected machine-level core ready: %+v", x)
	}
}
func TestMachineInstallOwnsIntegrationAdapters(t *testing.T) {
	config := t.TempDir()
	home := t.TempDir()
	t.Setenv("XDG_CONFIG_HOME", config)
	t.Setenv("HOME", home)
	t.Setenv("CLAUDE_CONFIG_DIR", "")
	t.Setenv("CODEX_HOME", "")

	if err := machineInstall(); err != nil {
		t.Fatal(err)
	}
	dir, err := integrationsDir()
	if err != nil {
		t.Fatal(err)
	}
	for _, name := range []string{"claude", "codex", "kiro"} {
		b, err := os.ReadFile(filepath.Join(dir, "taviq-"+name))
		if err != nil {
			t.Fatal(err)
		}
		if !strings.Contains(string(b), "' observe "+name+" agent") {
			t.Fatalf("unexpected %s adapter: %s", name, b)
		}
	}
	if err := machineUninstall(); err != nil {
		t.Fatal(err)
	}
	if _, err := os.Stat(dir); !os.IsNotExist(err) {
		t.Fatal("integration adapter directory must be removed")
	}
}

func TestKiroCrewAdapterUsesCrewMode(t *testing.T) {
	config := t.TempDir()
	home := t.TempDir()
	t.Setenv("XDG_CONFIG_HOME", config)
	t.Setenv("HOME", home)
	t.Setenv("CLAUDE_CONFIG_DIR", "")
	t.Setenv("CODEX_HOME", "")
	if err := machineInstall(); err != nil {
		t.Fatal(err)
	}
	dir, err := integrationsDir()
	if err != nil {
		t.Fatal(err)
	}
	b, err := os.ReadFile(filepath.Join(dir, "taviq-kiro-crew"))
	if err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(string(b), "' observe kiro crew") {
		t.Fatalf("unexpected Kiro Crew adapter: %s", b)
	}
}

func TestObserveIgnoresRepositoryWithoutMarker(t *testing.T) {
	dir := enterRepo(t)
	if err := observe("claude", "agent", ""); err != nil {
		t.Fatal(err)
	}
	path, err := runtimePath()
	if err != nil {
		t.Fatal(err)
	}
	if _, err := os.Stat(path); !os.IsNotExist(err) {
		t.Fatal("unmarked repository must not record observations")
	}
	if _, err := os.Stat(filepath.Join(dir, ".taviq")); !os.IsNotExist(err) {
		t.Fatal("observe must not create files in the working tree")
	}
}

func TestObserveKeepsWorkingTreeClean(t *testing.T) {
	enterRepo(t)
	if err := initMarker(); err != nil {
		t.Fatal(err)
	}
	if err := observe("claude", "agent", ""); err != nil {
		t.Fatal(err)
	}
	out, err := exec.Command("git", "status", "--porcelain", "--untracked-files=all").Output()
	if err != nil {
		t.Fatal(err)
	}
	if strings.TrimSpace(string(out)) != "?? .taviq.yml" {
		t.Fatalf("observe must not add untracked files: %q", out)
	}
}

func TestHookIgnoresProvenanceTextOutsideTrailers(t *testing.T) {
	dir := enterRepo(t)
	if err := initMarker(); err != nil {
		t.Fatal(err)
	}
	msg := filepath.Join(dir, "msg")
	body := "Change\n\n# ------------------------ >8 ------------------------\n# Do not modify or remove the line above.\ndiff --git a/x b/x\n+Taviq-Provenance: v1\n"
	_ = os.WriteFile(msg, []byte(body), 0o644)
	t.Setenv("TAVIQ_TOOL", "claude")
	if err := hook(msg); err != nil {
		t.Fatal(err)
	}
	b, _ := os.ReadFile(msg)
	if !strings.HasPrefix(string(b), "Change\n\nTaviq-Provenance: v1\nTaviq-Tools: claude\n\n# ---") {
		t.Fatalf("trailer must be added before the scissors line: %q", b)
	}
	if err := hook(msg); err != nil {
		t.Fatal(err)
	}
	again, _ := os.ReadFile(msg)
	if string(again) != string(b) {
		t.Fatalf("hook must not duplicate the trailer: %q", again)
	}
}

func TestMachineHooksChainRepositoryHooks(t *testing.T) {
	config := t.TempDir()
	home := t.TempDir()
	bin := t.TempDir()
	t.Setenv("XDG_CONFIG_HOME", config)
	t.Setenv("HOME", home)
	t.Setenv("CLAUDE_CONFIG_DIR", "")
	t.Setenv("CODEX_HOME", "")
	// Stand-in binary so the prepare-commit-msg shim does not run the test binary.
	_ = os.WriteFile(filepath.Join(bin, "taviq"), []byte("#!/bin/sh\necho taviq >> \"$3\"\n"), 0o755)
	t.Setenv("PATH", bin+string(os.PathListSeparator)+os.Getenv("PATH"))
	dir := enterRepo(t)
	configureGit()
	if err := machineInstall(); err != nil {
		t.Fatal(err)
	}
	hooks := filepath.Join(dir, ".git", "hooks")
	_ = os.WriteFile(filepath.Join(hooks, "pre-commit"), []byte("#!/bin/sh\ntouch pre-commit-ran\n"), 0o755)
	_ = os.WriteFile(filepath.Join(hooks, "commit-msg"), []byte("#!/bin/sh\necho local-commit-msg >> \"$1\"\n"), 0o755)
	_ = os.WriteFile("a", []byte("a"), 0o644)
	_ = exec.Command("git", "add", "a").Run()
	if out, err := exec.Command("git", "commit", "-m", "a").CombinedOutput(); err != nil {
		t.Fatalf("commit failed: %v %s", err, out)
	}
	if _, err := os.Stat(filepath.Join(dir, "pre-commit-ran")); err != nil {
		t.Fatal("repository pre-commit hook must still run")
	}
	msg, _ := exec.Command("git", "log", "-1", "--format=%B").Output()
	for _, want := range []string{"taviq", "local-commit-msg"} {
		if !strings.Contains(string(msg), want) {
			t.Fatalf("missing %q in commit message: %q", want, msg)
		}
	}

	_ = os.WriteFile(filepath.Join(hooks, "pre-commit"), []byte("#!/bin/sh\nexit 1\n"), 0o755)
	_ = os.WriteFile("b", []byte("b"), 0o644)
	_ = exec.Command("git", "add", "b").Run()
	if err := exec.Command("git", "commit", "-m", "b").Run(); err == nil {
		t.Fatal("a failing repository hook must still block the commit")
	}
	if err := machineUninstall(); err != nil {
		t.Fatal(err)
	}
}

func TestDoctorReportsRepositoryHooksPathOverride(t *testing.T) {
	config := t.TempDir()
	home := t.TempDir()
	t.Setenv("XDG_CONFIG_HOME", config)
	t.Setenv("HOME", home)
	t.Setenv("CLAUDE_CONFIG_DIR", "")
	t.Setenv("CODEX_HOME", "")
	enterRepo(t)
	if err := initMarker(); err != nil {
		t.Fatal(err)
	}
	if err := machineInstall(); err != nil {
		t.Fatal(err)
	}
	_ = exec.Command("git", "config", "core.hooksPath", ".husky").Run()
	x, err := diagnose()
	if err != nil {
		t.Fatal(err)
	}
	if x["core_ready"].(bool) || x["checks"].(map[string]bool)["no_repository_hooks_path"] {
		t.Fatalf("repository hooksPath bypasses the machine hook: %+v", x)
	}
}

func TestVersionPrefersStampedRelease(t *testing.T) {
	old := version
	t.Cleanup(func() { version = old })
	version = ""
	if got := taviqVersion(); got == "" {
		t.Fatal("unstamped build must still report a version")
	}
	version = "v0.1.0"
	if got := taviqVersion(); got != "v0.1.0" {
		t.Fatalf("got %q, want stamped v0.1.0", got)
	}
}

func TestDoctorReportsVersion(t *testing.T) {
	enterRepo(t)
	t.Setenv("HOME", t.TempDir())
	t.Setenv("CLAUDE_CONFIG_DIR", "")
	t.Setenv("CODEX_HOME", "")
	t.Setenv("XDG_CONFIG_HOME", t.TempDir())
	x, err := diagnose()
	if err != nil {
		t.Fatal(err)
	}
	if x["version"] != taviqVersion() {
		t.Fatalf("doctor version = %v, want %q", x["version"], taviqVersion())
	}
}
