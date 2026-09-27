package main

import (
	"encoding/json"
	"os"
	"path/filepath"
	"reflect"
	"strings"
	"testing"
)

const userClaudeSettings = `{
  "model": "opus",
  "hooks": {
    "PreToolUse": [
      {"matcher": "Bash", "hooks": [{"type": "command", "command": "check && echo <ok>"}]}
    ],
    "Stop": [
      {"hooks": [{"type": "command", "command": "notify"}]}
    ]
  }
}
`

func claudeSandbox(t *testing.T, settings string) string {
	t.Helper()
	t.Setenv("XDG_CONFIG_HOME", t.TempDir())
	t.Setenv("HOME", t.TempDir())
	dir := t.TempDir()
	t.Setenv("CLAUDE_CONFIG_DIR", dir)
	path := filepath.Join(dir, "settings.json")
	if settings != "" {
		if err := os.WriteFile(path, []byte(settings), 0o600); err != nil {
			t.Fatal(err)
		}
	}
	return path
}

func readJSON(t *testing.T, path string) map[string]any {
	t.Helper()
	b, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	var x map[string]any
	if err := json.Unmarshal(b, &x); err != nil {
		t.Fatal(err)
	}
	return x
}

func TestClaudeIntegrationPreservesUserSettings(t *testing.T) {
	path := claudeSandbox(t, userClaudeSettings)
	var original map[string]any
	_ = json.Unmarshal([]byte(userClaudeSettings), &original)

	for i := 0; i < 2; i++ {
		if err := installClaudeCodeIntegration(); err != nil {
			t.Fatal(err)
		}
	}
	b, _ := os.ReadFile(path)
	if n := strings.Count(string(b), claudeHookSubcommand); n != 1 {
		t.Fatalf("want exactly one Taviq hook after repeated install, got %d:\n%s", n, b)
	}
	if !strings.Contains(string(b), "check && echo <ok>") {
		t.Fatalf("user command was escaped or lost:\n%s", b)
	}
	if !claudeCodeIntegrationInstalled() {
		t.Fatal("doctor does not see the installed hook")
	}
	if info, _ := os.Stat(path); info.Mode().Perm() != 0o600 {
		t.Fatalf("settings mode changed to %v", info.Mode().Perm())
	}

	if err := uninstallClaudeCodeIntegration(); err != nil {
		t.Fatal(err)
	}
	if got := readJSON(t, path); !reflect.DeepEqual(got, original) {
		t.Fatalf("uninstall did not restore user settings:\n got %v\nwant %v", got, original)
	}
	if claudeCodeIntegrationInstalled() {
		t.Fatal("hook still reported after uninstall")
	}
}

func TestClaudeIntegrationRemovesOnlyItsOwnKeys(t *testing.T) {
	path := claudeSandbox(t, "")
	if err := installClaudeCodeIntegration(); err != nil {
		t.Fatal(err)
	}
	if err := uninstallClaudeCodeIntegration(); err != nil {
		t.Fatal(err)
	}
	if got := readJSON(t, path); len(got) != 0 {
		t.Fatalf("want empty settings after uninstall, got %v", got)
	}
}

func TestClaudeIntegrationSkipsMachineWithoutClaude(t *testing.T) {
	claudeSandbox(t, "")
	missing := filepath.Join(t.TempDir(), "absent")
	t.Setenv("CLAUDE_CONFIG_DIR", missing)
	if err := installClaudeCodeIntegration(); err != nil {
		t.Fatal(err)
	}
	if exists(missing) {
		t.Fatal("install created a Claude config directory")
	}
}

func TestClaudeIntegrationLeavesInvalidSettingsUntouched(t *testing.T) {
	broken := "{ not json"
	path := claudeSandbox(t, broken)
	if err := installClaudeCodeIntegration(); err == nil {
		t.Fatal("want visible failure on invalid settings")
	}
	if b, _ := os.ReadFile(path); string(b) != broken {
		t.Fatalf("invalid settings were rewritten: %q", b)
	}
}

func TestClaudeCodeHookObservesEventCwd(t *testing.T) {
	dir := enterRepo(t)
	if err := initMarker(); err != nil {
		t.Fatal(err)
	}
	if err := os.Chdir(t.TempDir()); err != nil {
		t.Fatal(err)
	}
	event, _ := json.Marshal(map[string]any{"cwd": dir, "tool_name": "Write", "tool_input": map[string]any{"content": "x"}})
	claudeCodeHook(strings.NewReader(string(event)))

	path, err := runtimePath()
	if err != nil {
		t.Fatal(err)
	}
	b, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	var x Runtime
	_ = json.Unmarshal(b, &x)
	if !reflect.DeepEqual(x.Tools, []string{"claude"}) || !reflect.DeepEqual(x.Modes, []string{"agent"}) || len(x.Models) != 0 {
		t.Fatalf("unexpected observation: %+v", x)
	}
}

func TestClaudeCodeHookIgnoresNonRepository(t *testing.T) {
	outside := t.TempDir()
	old, _ := os.Getwd()
	t.Cleanup(func() { _ = os.Chdir(old) })
	if err := os.Chdir(outside); err != nil {
		t.Fatal(err)
	}
	claudeCodeHook(strings.NewReader(`{"cwd":"` + outside + `"}`))
	claudeCodeHook(strings.NewReader("not json"))
	if entries, _ := os.ReadDir(outside); len(entries) != 0 {
		t.Fatalf("hook wrote outside a repository: %v", entries)
	}
}
