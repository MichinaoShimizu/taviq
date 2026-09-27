package main

import (
	"encoding/json"
	"os"
	"path/filepath"
	"reflect"
	"strings"
	"testing"
)

const userHooksFile = `{
  "model": "opus",
  "hooks": {
    "PreToolUse": [
      {"matcher": "Bash", "hooks": [{"type": "command", "command": "check && echo <ok>"}]},
      "unexpected"
    ],
    "Stop": [
      {"hooks": [{"type": "command", "command": "notify"}]}
    ]
  }
}
`

// agentSandbox points every tool config at temp dirs and returns the hooks
// file path of the integration under test.
func agentSandbox(t *testing.T, i agentHookIntegration, content string) string {
	t.Helper()
	t.Setenv("XDG_CONFIG_HOME", t.TempDir())
	t.Setenv("HOME", t.TempDir())
	t.Setenv("CLAUDE_CONFIG_DIR", t.TempDir())
	t.Setenv("CODEX_HOME", t.TempDir())
	path, err := i.path()
	if err != nil {
		t.Fatal(err)
	}
	if content != "" {
		if err := os.WriteFile(path, []byte(content), 0o600); err != nil {
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

func forEachIntegration(t *testing.T, f func(t *testing.T, i agentHookIntegration)) {
	for _, i := range agentHookIntegrations {
		t.Run(i.name, func(t *testing.T) { f(t, i) })
	}
}

func TestAgentHookPreservesUserSettings(t *testing.T) {
	forEachIntegration(t, func(t *testing.T, i agentHookIntegration) {
		path := agentSandbox(t, i, userHooksFile)
		var original map[string]any
		_ = json.Unmarshal([]byte(userHooksFile), &original)

		for n := 0; n < 2; n++ {
			if err := i.install(); err != nil {
				t.Fatal(err)
			}
		}
		b, _ := os.ReadFile(path)
		if n := strings.Count(string(b), i.subcommand); n != 1 {
			t.Fatalf("want exactly one Taviq hook after repeated install, got %d:\n%s", n, b)
		}
		if !strings.Contains(string(b), "check && echo <ok>") {
			t.Fatalf("user command was escaped or lost:\n%s", b)
		}
		if !i.installed() {
			t.Fatal("doctor does not see the installed hook")
		}
		if info, _ := os.Stat(path); info.Mode().Perm() != 0o600 {
			t.Fatalf("file mode changed to %v", info.Mode().Perm())
		}

		if err := i.uninstall(); err != nil {
			t.Fatal(err)
		}
		if got := readJSON(t, path); !reflect.DeepEqual(got, original) {
			t.Fatalf("uninstall did not restore user settings:\n got %v\nwant %v", got, original)
		}
		if i.installed() {
			t.Fatal("hook still reported after uninstall")
		}
	})
}

func TestAgentHookIntegrationsDoNotTouchEachOther(t *testing.T) {
	agentSandbox(t, claudeCodeIntegration, "")
	if err := installAgentHooks(); err != nil {
		t.Fatal(err)
	}
	for _, i := range agentHookIntegrations {
		path, _ := i.path()
		b, _ := os.ReadFile(path)
		for _, other := range agentHookIntegrations {
			if other.name != i.name && strings.Contains(string(b), other.subcommand) {
				t.Fatalf("%s file contains the %s hook:\n%s", i.name, other.name, b)
			}
		}
	}
	if err := uninstallAgentHooks(); err != nil {
		t.Fatal(err)
	}
	for _, i := range agentHookIntegrations {
		path, _ := i.path()
		if got := readJSON(t, path); len(got) != 0 {
			t.Fatalf("%s: want empty file after uninstall, got %v", i.name, got)
		}
	}
}

func TestAgentHookSkipsMachineWithoutTool(t *testing.T) {
	forEachIntegration(t, func(t *testing.T, i agentHookIntegration) {
		agentSandbox(t, i, "")
		missing := filepath.Join(t.TempDir(), "absent")
		t.Setenv("CLAUDE_CONFIG_DIR", missing)
		t.Setenv("CODEX_HOME", missing)
		if err := i.install(); err != nil {
			t.Fatal(err)
		}
		if exists(missing) {
			t.Fatal("install created a tool config directory")
		}
	})
}

func TestAgentHookLeavesInvalidSettingsUntouched(t *testing.T) {
	forEachIntegration(t, func(t *testing.T, i agentHookIntegration) {
		for _, broken := range []string{"{ not json", `{"hooks": []}`, `{"hooks": {"PreToolUse": {}}}`} {
			path := agentSandbox(t, i, broken)
			if err := i.install(); err == nil {
				t.Fatalf("want visible failure on %q", broken)
			}
			if b, _ := os.ReadFile(path); string(b) != broken {
				t.Fatalf("invalid settings were rewritten: %q", b)
			}
		}
	})
}

func observedRuntime(t *testing.T) Runtime {
	t.Helper()
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
	return x
}

func hookEventInRepo(t *testing.T, fields map[string]any) (string, string) {
	t.Helper()
	dir := enterRepo(t)
	if err := initMarker(); err != nil {
		t.Fatal(err)
	}
	if err := os.Chdir(t.TempDir()); err != nil {
		t.Fatal(err)
	}
	fields["cwd"] = dir
	event, _ := json.Marshal(fields)
	return dir, string(event)
}

func TestClaudeCodeHookObservesEventCwd(t *testing.T) {
	_, event := hookEventInRepo(t, map[string]any{"model": "claude-x", "tool_name": "Write", "tool_input": map[string]any{"content": "x"}})
	agentHook(strings.NewReader(event), "claude", false)
	x := observedRuntime(t)
	if !reflect.DeepEqual(x.Tools, []string{"claude"}) || !reflect.DeepEqual(x.Modes, []string{"agent"}) || len(x.Models) != 0 {
		t.Fatalf("unexpected observation: %+v", x)
	}
}

func TestCodexHookRecordsSuppliedModel(t *testing.T) {
	_, event := hookEventInRepo(t, map[string]any{"model": "gpt-5.3-codex", "tool_name": "Bash"})
	agentHook(strings.NewReader(event), "codex", true)
	x := observedRuntime(t)
	if !reflect.DeepEqual(x.Tools, []string{"codex"}) || !reflect.DeepEqual(x.Models, []string{"gpt-5.3-codex"}) {
		t.Fatalf("unexpected observation: %+v", x)
	}
}

func TestCodexHookDropsUnsafeModel(t *testing.T) {
	_, event := hookEventInRepo(t, map[string]any{"model": "a,b\nTaviq-Tools: forged"})
	agentHook(strings.NewReader(event), "codex", true)
	if x := observedRuntime(t); len(x.Models) != 0 {
		t.Fatalf("unsafe model recorded: %+v", x)
	}
}

func TestAgentHookIgnoresNonRepository(t *testing.T) {
	outside := t.TempDir()
	old, _ := os.Getwd()
	t.Cleanup(func() { _ = os.Chdir(old) })
	if err := os.Chdir(outside); err != nil {
		t.Fatal(err)
	}
	agentHook(strings.NewReader(`{"cwd":"`+outside+`"}`), "codex", true)
	agentHook(strings.NewReader("not json"), "claude", false)
	if entries, _ := os.ReadDir(outside); len(entries) != 0 {
		t.Fatalf("hook wrote outside a repository: %v", entries)
	}
}
