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
	_ = os.Mkdir(filepath.Join(dir, ".taviq"), 0o755)
	_ = os.WriteFile(filepath.Join(dir, ".taviq", "runtime.json"), []byte(`{"tools":["codex","claude"],"modes":["agent"],"models":["z","a"]}`), 0o644)
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
	dir := enterRepo(t)
	configureGit()
	_ = os.WriteFile("a", []byte("a"), 0o644)
	_ = exec.Command("git", "add", "a").Run()
	_ = exec.Command("git", "commit", "-m", "a").Run()

	_ = observe("claude", "agent", "sonnet")
	_ = observe("codex", "agent", "gpt-x")
	_ = observe("claude", "agent", "sonnet")
	b, _ := os.ReadFile(filepath.Join(dir, ".taviq", "runtime.json"))
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
	b, _ = os.ReadFile(filepath.Join(dir, ".taviq", "runtime.json"))
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
	t.Setenv("XDG_CONFIG_HOME", config)

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
\n
func TestMachineInstallOwnsIntegrationAdapters(t *testing.T) {
	config := t.TempDir()
	home := t.TempDir()
	t.Setenv("XDG_CONFIG_HOME", config)
	t.Setenv("HOME", home)

	if err := machineInstall(); err != nil {
		t.Fatal(err)
	}
	dir, err := integrationsDir()
	if err != nil {
		t.Fatal(err)
	}
	for _, name := range []string{"claude", "codex", "kiro"} {
		b, err := os.ReadFile(filepath.Join(dir, name))
		if err != nil {
			t.Fatal(err)
		}
		if !strings.Contains(string(b), "taviq observe "+name+" agent") {
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
